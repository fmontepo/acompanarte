# app/services/embedding_batch.py
# Batch job de embeddings clínicos para RAG interno del terapeuta.
#
# Estrategia de detección de cambios:
#   Cada registro almacena embedding_hash = SHA-256(texto_a_embedear).
#   El job compara el hash actual del texto con el almacenado.
#   Si coincide → skip (sin cambios). Si difiere → regenera embedding.
#
# Textos embedeados:
#   registros_seguimiento : "[tipo] [fecha]\n[contenido_enc]"
#   actividades_familiar  : "[titulo]\nObjetivo: [objetivo]\n[descripcion]"
#   progreso_actividad    : "Sesión: [actividad.titulo]\n..." (solo si tiene observacion)

import asyncio
import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.registroSeguimiento import RegistroSeguimiento
from app.models.actividadFamiliar import ActividadFamiliar
from app.models.progresoActividad import ProgresoActividad

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Construcción de texto fuente para cada tipo de dato clínico
# ──────────────────────────────────────────────────────────────────────────────

def _texto_registro(r: RegistroSeguimiento) -> str:
    partes = [f"Tipo: {r.tipo}", f"Fecha: {r.fecha_registro}"]
    if r.contenido_enc:
        partes.append(r.contenido_enc)
    return "\n".join(partes)


def _texto_actividad(a: ActividadFamiliar) -> str:
    partes = [f"Actividad: {a.titulo}"]
    if a.objetivo:
        partes.append(f"Objetivo: {a.objetivo}")
    if a.descripcion:
        partes.append(a.descripcion)
    partes.append(f"Frecuencia: {a.frecuencia}")
    return "\n".join(partes)


def _texto_progreso(p: ProgresoActividad, titulo_actividad: str) -> str:
    partes = [f"Sesión de actividad: {titulo_actividad}"]
    resultado = "Completa" if p.es_completada else f"Parcial ({p.etapas_completadas or 0} etapas)"
    partes.append(f"Resultado: {resultado}")
    if p.nivel_satisfaccion:
        partes.append(f"Satisfacción: {p.nivel_satisfaccion}/5")
    if p.observacion:
        partes.append(f"Observación: {p.observacion}")
    return "\n".join(partes)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _hash(texto: str) -> str:
    """SHA-256 truncado a 64 chars — identificador único del contenido."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


async def _embed_texto(model, texto: str) -> list[float]:
    """Ejecuta model.encode() en thread pool para no bloquear el event loop."""
    vector = await asyncio.to_thread(model.encode, texto)
    return vector.tolist()


# ──────────────────────────────────────────────────────────────────────────────
# Procesadores por tabla
# ──────────────────────────────────────────────────────────────────────────────

async def _procesar_registros(db, model) -> int:
    """Embede registros_seguimiento con cambios desde el último batch."""
    res = await db.execute(select(RegistroSeguimiento))
    registros = res.scalars().all()

    actualizados = 0
    for r in registros:
        texto = _texto_registro(r)
        nuevo_hash = _hash(texto)
        if r.embedding_hash == nuevo_hash:
            continue  # sin cambios — skip
        r.embedding = await _embed_texto(model, texto)
        r.embedding_hash = nuevo_hash
        actualizados += 1

    if actualizados:
        await db.commit()
    return actualizados


async def _procesar_actividades(db, model) -> int:
    """Embede actividades_familiar con cambios desde el último batch."""
    res = await db.execute(select(ActividadFamiliar))
    actividades = res.scalars().all()

    actualizados = 0
    for a in actividades:
        texto = _texto_actividad(a)
        nuevo_hash = _hash(texto)
        if a.embedding_hash == nuevo_hash:
            continue
        a.embedding = await _embed_texto(model, texto)
        a.embedding_hash = nuevo_hash
        actualizados += 1

    if actualizados:
        await db.commit()
    return actualizados


async def _procesar_progresos(db, model) -> int:
    """
    Embede progreso_actividad — solo registros con observacion.
    Carga la actividad relacionada para incluir su título en el texto.
    """
    res = await db.execute(
        select(ProgresoActividad)
        .where(ProgresoActividad.observacion.is_not(None))
        .options(selectinload(ProgresoActividad.actividad))
    )
    progresos = res.scalars().all()

    actualizados = 0
    for p in progresos:
        titulo = p.actividad.titulo if p.actividad else "Actividad"
        texto = _texto_progreso(p, titulo)
        nuevo_hash = _hash(texto)
        if p.embedding_hash == nuevo_hash:
            continue
        p.embedding = await _embed_texto(model, texto)
        p.embedding_hash = nuevo_hash
        actualizados += 1

    if actualizados:
        await db.commit()
    return actualizados


# ──────────────────────────────────────────────────────────────────────────────
# Punto de entrada principal del batch
# ──────────────────────────────────────────────────────────────────────────────

async def ejecutar_batch_embedding() -> dict:
    """
    Job principal: detecta y procesa registros clínicos sin embedding o con
    contenido modificado desde el último run. Seguro para ejecutar en paralelo
    con el servidor (usa su propia sesión de DB).

    Retorna un dict con estadísticas del run.
    """
    from app.services.ia_service import get_embedding_model

    inicio = datetime.now(timezone.utc)
    log.info("[Batch] Iniciando job de embeddings clínicos — %s", inicio.isoformat())

    stats: dict = {
        "inicio": inicio.isoformat(),
        "registros_actualizados": 0,
        "actividades_actualizadas": 0,
        "progresos_actualizados": 0,
        "errores": [],
        "duracion_seg": 0,
    }

    try:
        model = get_embedding_model()
    except Exception as e:
        msg = f"No se pudo cargar el modelo de embeddings: {e}"
        log.error("[Batch] %s", msg)
        stats["errores"].append(msg)
        return stats

    async with AsyncSessionLocal() as db:

        # 1 — Registros de seguimiento
        try:
            stats["registros_actualizados"] = await _procesar_registros(db, model)
            log.info("[Batch] registros_seguimiento: %d actualizados",
                     stats["registros_actualizados"])
        except Exception as e:
            msg = f"Error en registros_seguimiento: {e}"
            log.exception("[Batch] %s", msg)
            stats["errores"].append(msg)

        # 2 — Actividades familiares
        try:
            stats["actividades_actualizadas"] = await _procesar_actividades(db, model)
            log.info("[Batch] actividades_familiar: %d actualizadas",
                     stats["actividades_actualizadas"])
        except Exception as e:
            msg = f"Error en actividades_familiar: {e}"
            log.exception("[Batch] %s", msg)
            stats["errores"].append(msg)

        # 3 — Progresos de actividad (solo con observacion)
        try:
            stats["progresos_actualizados"] = await _procesar_progresos(db, model)
            log.info("[Batch] progreso_actividad: %d actualizados",
                     stats["progresos_actualizados"])
        except Exception as e:
            msg = f"Error en progreso_actividad: {e}"
            log.exception("[Batch] %s", msg)
            stats["errores"].append(msg)

    fin = datetime.now(timezone.utc)
    stats["duracion_seg"] = round((fin - inicio).total_seconds(), 1)
    log.info("[Batch] Completado en %.1f s — %s", stats["duracion_seg"], stats)
    return stats
