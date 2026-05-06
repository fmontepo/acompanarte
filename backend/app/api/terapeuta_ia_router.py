# app/api/terapeuta_ia_router.py
# Módulo IA para terapeutas internos
# Endpoints:
#   GET  /ia/terapeuta/stats  → métricas analíticas de los pacientes del terapeuta
#   POST /ia/terapeuta/chat   → chat clínico con contexto de pacientes reales

from datetime import date, timedelta
from typing import Optional
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.db.session import get_db
from app.api.deps import CurrentUser, require_roles
from app.models.terapeuta import Terapeuta
from app.models.equipoTerapeutico import EquipoTerapeutico
from app.models.miembroEquipo import MiembroEquipo
from app.models.paciente import Paciente
from app.models.registroSeguimiento import RegistroSeguimiento
from app.models.actividadFamiliar import ActividadFamiliar
from app.models.progresoActividad import ProgresoActividad

router = APIRouter(
    prefix="/ia/terapeuta",
    tags=["IA — Terapeuta"],
    dependencies=[Depends(require_roles("ter-int", "admin"))],
)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

PESOS_BIENESTAR = {
    "logro": 100, "objetivo": 75, "evolucion": 65,
    "observacion": 55, "incidente": 25,
}

LABELS_TIPO = {
    "logro": "Logro", "objetivo": "Objetivo cumplido",
    "evolucion": "Evolución", "observacion": "Observación",
    "incidente": "Incidente",
}


def _bienestar(registros: list) -> int | None:
    vals = [PESOS_BIENESTAR.get(r.tipo, 60) for r in registros]
    return round(sum(vals) / len(vals)) if vals else None


async def _get_terapeuta(db: AsyncSession, usuario_id) -> Terapeuta | None:
    q = await db.execute(select(Terapeuta).where(Terapeuta.usuario_id == usuario_id))
    return q.scalar_one_or_none()


async def _pacientes_del_terapeuta(db: AsyncSession, terapeuta_id) -> list[Paciente]:
    """Devuelve los pacientes activos cuyo equipo terapéutico incluye al terapeuta."""
    q = await db.execute(
        select(Paciente)
        .join(EquipoTerapeutico, EquipoTerapeutico.paciente_id == Paciente.id)
        .join(MiembroEquipo, MiembroEquipo.equipo_id == EquipoTerapeutico.id)
        .where(
            MiembroEquipo.terapeuta_id == terapeuta_id,
            EquipoTerapeutico.activo == True,
            Paciente.activo == True,
        )
        .options(selectinload(Paciente.diagnostico))
        .distinct()
    )
    return q.scalars().all()


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/ia/terapeuta/stats
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/stats", summary="Métricas analíticas del terapeuta sobre sus pacientes")
async def stats_terapeuta(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    terapeuta = await _get_terapeuta(db, current_user.id)
    if not terapeuta:
        raise HTTPException(403, detail="Solo terapeutas pueden acceder a este recurso")

    pacientes = await _pacientes_del_terapeuta(db, terapeuta.id)
    if not pacientes:
        return {
            "total_pacientes": 0,
            "diagnosticos": [],
            "bienestar_promedio": None,
            "registros_tipos": [],
            "actividades_efectividad": [],
            "evolucion_bienestar": [],
        }

    pac_ids = [p.id for p in pacientes]

    # ── 1. Distribución de diagnósticos ──────────────────────────────────────
    diag_counter: Counter = Counter()
    for p in pacientes:
        label = (p.diagnostico.nombre if p.diagnostico else None) or "Sin diagnóstico"
        diag_counter[label] += 1
    diagnosticos = [
        {"nombre": k, "cantidad": v, "porcentaje": round(v / len(pacientes) * 100)}
        for k, v in diag_counter.most_common()
    ]

    # ── 2. Distribución de tipos de registro ─────────────────────────────────
    reg_q = await db.execute(
        select(RegistroSeguimiento.tipo, func.count().label("n"))
        .where(RegistroSeguimiento.paciente_id.in_(pac_ids))
        .group_by(RegistroSeguimiento.tipo)
        .order_by(func.count().desc())
    )
    total_regs = 0
    tipos_raw = reg_q.all()
    for _, n in tipos_raw:
        total_regs += n
    registros_tipos = [
        {
            "tipo": t,
            "label": LABELS_TIPO.get(t, t.capitalize()),
            "cantidad": n,
            "porcentaje": round(n / total_regs * 100) if total_regs else 0,
        }
        for t, n in tipos_raw
    ]

    # ── 3. Bienestar promedio del grupo ───────────────────────────────────────
    # Últimos 10 registros por paciente → bienestar individual → promedio global
    bienestar_vals = []
    for p_id in pac_ids:
        rq = await db.execute(
            select(RegistroSeguimiento)
            .where(RegistroSeguimiento.paciente_id == p_id)
            .order_by(RegistroSeguimiento.fecha_registro.desc())
            .limit(10)
        )
        b = _bienestar(rq.scalars().all())
        if b is not None:
            bienestar_vals.append(b)
    bienestar_promedio = round(sum(bienestar_vals) / len(bienestar_vals)) if bienestar_vals else None

    # ── 4. Actividades y su efectividad ─────────────────────────────────────
    # Para cada actividad: veces completadas vs. días activa (tasa de cumplimiento)
    act_q = await db.execute(
        select(ActividadFamiliar)
        .where(
            ActividadFamiliar.terapeuta_id == terapeuta.id,
            ActividadFamiliar.paciente_id.in_(pac_ids),
            ActividadFamiliar.activa == True,
        )
    )
    actividades = act_q.scalars().all()

    efectividad = []
    for act in actividades:
        prog_q = await db.execute(
            select(
                ProgresoActividad.es_completada,
                ProgresoActividad.etapas_completadas,
            )
            .where(ProgresoActividad.actividad_id == act.id)
        )
        sesiones = prog_q.all()
        veces = len(sesiones)
        veces_plenas = sum(1 for s in sesiones if s.es_completada)

        # Etapas efectivas = suma de (total_etapas si completa, else etapas_completadas)
        etapas_efectivas = sum(
            act.total_etapas if s.es_completada else (s.etapas_completadas or 0)
            for s in sesiones
        )

        # Días activa desde creación (para calcular tasa)
        dias_activa = max(
            1,
            (date.today() - act.creado_en.date()).days if act.creado_en else 1
        )
        # Completions esperadas según frecuencia
        esperadas = {
            "diaria": dias_activa,
            "semanal": max(1, dias_activa // 7),
            "quincenal": max(1, dias_activa // 15),
            "libre": max(1, dias_activa // 7),
        }.get(act.frecuencia or "libre", max(1, dias_activa // 7))

        etapas_esperadas = act.total_etapas * esperadas
        tasa = min(100, round(etapas_efectivas / etapas_esperadas * 100)) if etapas_esperadas > 0 else 0

        efectividad.append({
            "id":               str(act.id),
            "titulo":           act.titulo,
            "paciente_id":      str(act.paciente_id),
            "frecuencia":       act.frecuencia or "libre",
            "total_etapas":     act.total_etapas,
            "veces_completada": veces,
            "veces_plenas":     veces_plenas,
            "tasa_cumplimiento": tasa,
        })

    # Ordenar por tasa de cumplimiento desc
    efectividad.sort(key=lambda x: x["tasa_cumplimiento"], reverse=True)

    # ── 5. Evolución de bienestar últimas 8 semanas ──────────────────────────
    evolucion = []
    hoy = date.today()
    for semana in range(7, -1, -1):
        inicio = hoy - timedelta(weeks=semana + 1)
        fin    = hoy - timedelta(weeks=semana)
        label  = f"Sem {8 - semana}"

        vals_semana = []
        for p_id in pac_ids:
            rq = await db.execute(
                select(RegistroSeguimiento)
                .where(
                    RegistroSeguimiento.paciente_id == p_id,
                    RegistroSeguimiento.fecha_registro >= inicio,
                    RegistroSeguimiento.fecha_registro < fin,
                )
            )
            b = _bienestar(rq.scalars().all())
            if b is not None:
                vals_semana.append(b)

        evolucion.append({
            "semana": label,
            "fecha_inicio": inicio.isoformat(),
            "bienestar": round(sum(vals_semana) / len(vals_semana)) if vals_semana else None,
        })

    return {
        "total_pacientes": len(pacientes),
        "diagnosticos": diagnosticos,
        "bienestar_promedio": bienestar_promedio,
        "registros_tipos": registros_tipos,
        "actividades_efectividad": efectividad[:10],   # top 10
        "evolucion_bienestar": evolucion,
    }


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/ia/terapeuta/chat
# ──────────────────────────────────────────────────────────────────────────────

class ChatTerapeutaRequest(BaseModel):
    mensaje: str
    sesion_id: Optional[str] = None


class ChatTerapeutaResponse(BaseModel):
    respuesta: str
    fuentes: list = []
    sesion_id: Optional[str] = None


@router.post("/chat", response_model=ChatTerapeutaResponse, summary="Chat clínico con IA")
async def chat_terapeuta(
    body: ChatTerapeutaRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    if not body.mensaje or not body.mensaje.strip():
        raise HTTPException(422, detail="El mensaje no puede estar vacío")

    terapeuta = await _get_terapeuta(db, current_user.id)
    if not terapeuta:
        raise HTTPException(403, detail="Solo terapeutas pueden acceder a este recurso")

    try:
        from app.services.ia_service import (
            anonimizar_pii,
            cargar_reglas,
            buscar_contexto_rag,
            buscar_contexto_rag_clinico,
            generar_respuesta_ollama,
            aplicar_filtro_diagnostico,
        )

        mensaje_anonimo = anonimizar_pii(body.mensaje.strip())

        # Cargar reglas activas para contexto terapeuta (+ global)
        reglas = await cargar_reglas(db, contexto="terapeuta")

        # Construir contexto clínico estructurado (SQL) con datos reales
        pacientes = await _pacientes_del_terapeuta(db, terapeuta.id)
        contexto_clinico = await _construir_contexto_clinico(db, terapeuta.id, pacientes)
        pac_ids = [p.id for p in pacientes]

        # RAG bibliográfico — recursos profesionales validados
        fuentes_biblio = await buscar_contexto_rag(db, mensaje_anonimo)

        # RAG clínico — embeddings de registros, actividades y progresos
        # Acotado a los pacientes propios del terapeuta
        fuentes_clinicas = await buscar_contexto_rag_clinico(db, mensaje_anonimo, pac_ids)

        # Construir prompt con dual RAG
        prompt = _construir_prompt_terapeuta(
            mensaje_anonimo, contexto_clinico,
            fuentes_biblio, fuentes_clinicas, reglas,
        )
        respuesta = await generar_respuesta_ollama(prompt)
        respuesta, _ = aplicar_filtro_diagnostico(respuesta)

        return ChatTerapeutaResponse(
            respuesta=respuesta,
            fuentes=[{"titulo": f["titulo"], "score": f["score"]} for f in fuentes_biblio],
        )

    except Exception as e:
        import logging
        logging.error(f"[IA Terapeuta] Error: {e}")
        return ChatTerapeutaResponse(
            respuesta=(
                "El asistente clínico está disponible. Podés consultarme sobre "
                "el historial de tus pacientes, tendencias de bienestar, "
                "efectividad de actividades o estrategias terapéuticas.\n\n"
                "En este momento el módulo de IA local no está disponible — "
                "verificá que Ollama esté corriendo."
            ),
            fuentes=[],
        )


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/ia/terapeuta/batch/embedding — trigger manual del batch
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/batch/embedding",
    summary="Ejecutar batch de embeddings clínicos manualmente",
    description=(
        "Inicia el job de generación de embeddings sobre registros, actividades "
        "y progresos. Solo procesa registros con cambios desde el último run. "
        "Operación potencialmente lenta (depende del volumen de datos y el modelo)."
    ),
)
async def trigger_batch_embedding(current_user: CurrentUser):
    from app.services.scheduler import trigger_manual
    stats = await trigger_manual()
    return {
        "mensaje": "Batch de embeddings clínicos completado.",
        "stats": stats,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Helpers internos para el chat
# ──────────────────────────────────────────────────────────────────────────────

async def _construir_contexto_clinico(
    db: AsyncSession,
    terapeuta_id,
    pacientes: list[Paciente],
    max_registros_por_paciente: int = 5,
) -> str:
    """
    Genera un resumen anonimizado del estado clínico de los pacientes
    para inyectarlo en el prompt del chat.
    """
    if not pacientes:
        return "El terapeuta no tiene pacientes activos asignados."

    lineas = [f"Total de pacientes activos: {len(pacientes)}\n"]
    for idx, p in enumerate(pacientes, 1):
        diag = (p.diagnostico.nombre if p.diagnostico else "Sin diagnóstico")

        # Últimos registros del paciente
        rq = await db.execute(
            select(RegistroSeguimiento)
            .where(RegistroSeguimiento.paciente_id == p.id)
            .order_by(RegistroSeguimiento.fecha_registro.desc())
            .limit(max_registros_por_paciente)
        )
        registros = rq.scalars().all()
        bienestar = _bienestar(registros)

        # Actividades asignadas por este terapeuta a este paciente
        aq = await db.execute(
            select(ActividadFamiliar)
            .where(
                ActividadFamiliar.paciente_id == p.id,
                ActividadFamiliar.terapeuta_id == terapeuta_id,
                ActividadFamiliar.activa == True,
            )
        )
        actividades = aq.scalars().all()

        lineas.append(f"[Paciente {idx}]")
        lineas.append(f"  Diagnóstico: {diag}")
        lineas.append(f"  Bienestar estimado: {bienestar}%" if bienestar else "  Bienestar: sin datos")
        lineas.append(f"  Actividades activas: {len(actividades)}")

        # Cumplimiento de actividades con datos de etapas
        if actividades:
            lineas.append(f"  Detalle de actividades:")
            for act in actividades:
                prog_q = await db.execute(
                    select(
                        ProgresoActividad.es_completada,
                        ProgresoActividad.etapas_completadas,
                    )
                    .where(ProgresoActividad.actividad_id == act.id)
                )
                sesiones = prog_q.all()
                veces = len(sesiones)
                etapas_efectivas = sum(
                    act.total_etapas if s.es_completada else (s.etapas_completadas or 0)
                    for s in sesiones
                )
                dias = max(1, (date.today() - act.creado_en.date()).days if act.creado_en else 1)
                esperadas = {
                    "diaria": dias, "semanal": max(1, dias // 7),
                    "quincenal": max(1, dias // 15), "libre": max(1, dias // 7),
                }.get(act.frecuencia or "libre", max(1, dias // 7))
                etapas_esperadas = act.total_etapas * esperadas
                tasa = min(100, round(etapas_efectivas / etapas_esperadas * 100)) if etapas_esperadas > 0 else 0
                etapas_info = f" | {act.total_etapas} etapas" if act.total_etapas > 1 else ""
                lineas.append(
                    f"    • '{act.titulo}' [{act.frecuencia}{etapas_info}] — "
                    f"cumplimiento: {tasa}% ({veces} sesiones registradas)"
                )

        if registros:
            lineas.append(f"  Últimos registros ({len(registros)}):")
            for r in registros:
                tipo_label = LABELS_TIPO.get(r.tipo, r.tipo)
                fecha_str = r.fecha_registro.strftime("%d/%m/%Y") if r.fecha_registro else "—"
                contenido_preview = (r.contenido_enc or "")[:200]
                lineas.append(f"    • [{fecha_str}] {tipo_label}: {contenido_preview}")
        lineas.append("")

    return "\n".join(lineas)


def _construir_prompt_terapeuta(
    consulta: str,
    contexto_clinico: str,
    fuentes_biblio: list[dict],
    fuentes_clinicas: list[dict] | None = None,
    reglas: dict | None = None,
    max_chars_fuente: int = 600,
) -> str:
    from app.services.ia_service import _bloque_reglas

    # Bloque bibliográfico
    biblio = "\n\n".join(
        f"[{f['titulo']}]\n{f['contenido'][:max_chars_fuente]}" for f in fuentes_biblio
    ) if fuentes_biblio else "No se encontró bibliografía relevante para esta consulta."

    # Bloque RAG clínico — fragmentos semánticamente cercanos a la consulta
    ETIQUETAS = {"registro": "Nota clínica", "actividad": "Actividad", "progreso": "Sesión registrada"}
    if fuentes_clinicas:
        rag_clinico = "\n\n".join(
            f"[{ETIQUETAS.get(f['fuente'], f['fuente'])}]\n{f['texto']}"
            for f in fuentes_clinicas
        )
    else:
        rag_clinico = "No se encontraron fragmentos clínicos semánticamente relevantes."

    bloque_reglas = _bloque_reglas(reglas or {})
    reglas_section = f"\n{bloque_reglas}\n" if bloque_reglas else ""

    return f"""Sos un asistente clínico de apoyo para terapeutas especializados.
Tu rol es analizar información clínica, identificar patrones, sugerir estrategias y responder consultas profesionales.
Tenés acceso al historial anonimizado de los pacientes del terapeuta.
Respondé con precisión clínica, en español profesional.
NO emitás diagnósticos definitivos — podés señalar patrones y sugerir evaluaciones.
{reglas_section}
--- CONTEXTO CLÍNICO ESTRUCTURADO (TODOS LOS PACIENTES) ---
{contexto_clinico}
--- FIN CONTEXTO ESTRUCTURADO ---

--- FRAGMENTOS CLÍNICOS RELEVANTES A LA CONSULTA (RAG) ---
{rag_clinico}
--- FIN FRAGMENTOS CLÍNICOS ---

--- BIBLIOGRAFÍA PROFESIONAL RELEVANTE ---
{biblio}
--- FIN BIBLIOGRAFÍA ---

Consulta del terapeuta:
{consulta}

Respondé de forma estructurada. Si la consulta involucra un paciente específico, referite a él como "Paciente 1", "Paciente 2", etc. para mantener la anonimidad del registro."""
