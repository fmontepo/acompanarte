# app/api/dashboard_router.py
# Endpoints de agregación para los dashboards de cada rol.
# Todos los valores se calculan desde la BD — sin datos hardcodeados.

from typing import Annotated
from datetime import datetime, timezone, timedelta, date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from sqlalchemy.orm import joinedload

from app.db.session import get_db
from app.api.deps import CurrentUser, require_roles
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.paciente import Paciente
from app.models.familiar import Familiar
from app.models.terapeuta import Terapeuta
from app.models.vinculoPaciente import VinculoPaciente
from app.models.actividadFamiliar import ActividadFamiliar
from app.models.registroSeguimiento import RegistroSeguimiento
from app.models.alerta import Alerta
from app.models.miembroEquipo import MiembroEquipo
from app.models.equipoTerapeutico import EquipoTerapeutico
from app.models.progresoActividad import ProgresoActividad
from app.models.recursoProfesional import RecursoProfesional
from app.models.parentesco import Parentesco

router = APIRouter(tags=["Dashboards"])

DBDep = Annotated[AsyncSession, Depends(get_db)]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _av_class(nombre: str) -> str:
    COLORS = ["av-tl", "av-pp", "av-bu", "av-am", "av-rd"]
    idx = sum(ord(c) for c in (nombre or "")) % len(COLORS)
    return COLORS[idx]


def _initials(nombre: str, apellido: str = "") -> str:
    n = (nombre or "")[:1].upper()
    a = (apellido or "")[:1].upper()
    return f"{n}{a}" or "?"


def _calcular_edad(fecha_nacimiento) -> int | None:
    """Calcula edad en años a partir de fecha_nacimiento (Date)."""
    if not fecha_nacimiento:
        return None
    hoy = date.today()
    años = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        años -= 1
    return años


def _bienestar_desde_registros(registros: list) -> int | None:
    """
    Calcula un índice de bienestar (0-100) basado en el tipo
    de los últimos registros de seguimiento.
      logro      → 100
      objetivo   → 75
      evolucion  → 65
      observacion→ 55
      incidente  → 25
    Retorna None si no hay registros.
    """
    if not registros:
        return None
    PESOS = {
        "logro":       100,
        "objetivo":    75,
        "evolucion":   65,
        "observacion": 55,
        "incidente":   25,
    }
    valores = [PESOS.get(r.tipo, 60) for r in registros]
    return round(sum(valores) / len(valores))


def _bienestar_label(score: int | None) -> str:
    if score is None:
        return "Sin datos"
    if score >= 80:
        return "Muy bien"
    if score >= 65:
        return "Estable"
    if score >= 45:
        return "Atención"
    return "Requiere seguimiento"


def _formato_fecha_relativa(dt) -> str | None:
    """Devuelve fecha relativa legible, p.ej. 'Hoy', 'Ayer', '3 días atrás'."""
    if dt is None:
        return None
    # dt puede ser date o datetime
    if hasattr(dt, 'date'):
        d = dt.date()
    else:
        d = dt
    hoy = date.today()
    delta = (hoy - d).days
    if delta == 0:
        return "Hoy"
    if delta == 1:
        return "Ayer"
    if delta < 7:
        return f"Hace {delta} días"
    if delta < 30:
        semanas = delta // 7
        return f"Hace {semanas} semana{'s' if semanas > 1 else ''}"
    meses = delta // 30
    return f"Hace {meses} mes{'es' if meses > 1 else ''}"


def _frecuencia_label(frecuencia: str) -> str:
    return {
        "diaria":     "Diaria",
        "semanal":    "Semanal",
        "quincenal":  "Quincenal",
        "libre":      "Libre",
    }.get(frecuencia or "", "Libre")


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN DASHBOARD  —  GET /api/v1/admin/dashboard
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/admin/dashboard",
    summary="Dashboard agregado para administración",
    dependencies=[Depends(require_roles("admin"))],
)
async def admin_dashboard(current_user: CurrentUser, db: DBDep):
    ahora = datetime.now(timezone.utc)
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total usuarios
    total_usuarios = (await db.execute(select(func.count(Usuario.id)))).scalar() or 0

    # Usuarios nuevos este mes
    nuevos_mes = (await db.execute(
        select(func.count(Usuario.id))
        .where(Usuario.creado_en >= inicio_mes)
    )).scalar() or 0

    # Usuarios por rol
    rol_counts_q = await db.execute(
        select(Rol.key, func.count(Usuario.id))
        .join(Usuario, Usuario.rol_id == Rol.id)
        .group_by(Rol.key)
    )
    rol_counts = {row[0]: row[1] for row in rol_counts_q.all()}

    # Total pacientes
    total_pacientes = (await db.execute(
        select(func.count(Paciente.id))
    )).scalar() or 0

    # Pacientes dados de alta este mes
    alta_este_mes = (await db.execute(
        select(func.count(Paciente.id))
        .where(Paciente.creado_en >= inicio_mes)
    )).scalar() or 0

    # Progreso completado hoy (actividades)
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    actividades_hoy = (await db.execute(
        select(func.count(ProgresoActividad.id))
        .where(ProgresoActividad.completada_en >= inicio_hoy)
    )).scalar() or 0

    # Usuarios recientes (últimos 5)
    recientes_q = await db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .order_by(Usuario.creado_en.desc())
        .limit(5)
    )
    recientes = recientes_q.scalars().all()

    # Recursos pendientes de validación
    pendientes_q = await db.execute(
        select(RecursoProfesional)
        .where(RecursoProfesional.validado == False, RecursoProfesional.activo == True)
        .order_by(RecursoProfesional.subido_en.desc())
        .limit(20)
    )
    pendientes = pendientes_q.scalars().all()

    return {
        "stats": {
            "usuarios": {
                "total":      total_usuarios,
                "nuevos_mes": nuevos_mes,
            },
            "pacientes": {
                "total":          total_pacientes,
                "activos":        total_pacientes,
                "alta_este_mes":  alta_este_mes,
            },
            "terapeutas": {
                "total":    rol_counts.get("ter-int", 0) + rol_counts.get("ter-ext", 0),
                "internos": rol_counts.get("ter-int", 0),
                "externos": rol_counts.get("ter-ext", 0),
            },
            "actividades_hoy": actividades_hoy,
        },
        "recientes": [
            {
                "id":        str(u.id),
                "nombre":    f"{u.nombre} {u.apellido}",
                "email":     u.email,
                "rol":       u.rol.key if u.rol else "",
                "rol_label": u.rol.label if u.rol else "",
                "fecha":     u.creado_en.isoformat() if u.creado_en else None,
            }
            for u in recientes
        ],
        "recursos_pendientes": [
            {
                "id":              str(r.id),
                "titulo":          r.titulo,
                "tipo":            r.tipo,
                "descripcion":     r.descripcion or "",
                "contenido_texto": r.contenido_texto or "",
                "subido_en":       r.subido_en.isoformat() if r.subido_en else None,
            }
            for r in pendientes
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# FAMILIAR DASHBOARD  —  GET /api/v1/familiar/dashboard
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/familiar/dashboard", summary="Dashboard agregado para familiar")
async def familiar_dashboard(current_user: CurrentUser, db: DBDep):
    familiar_q = await db.execute(
        select(Familiar).where(Familiar.usuario_id == current_user.id)
    )
    familiar = familiar_q.scalar_one_or_none()
    if not familiar:
        return {"paciente": None, "actividades_hoy": [], "seguimientos": [], "alertas": []}

    vinculo_q = await db.execute(
        select(VinculoPaciente)
        .where(VinculoPaciente.familiar_id == familiar.id, VinculoPaciente.activo == True)
        .limit(1)
    )
    vinculo = vinculo_q.scalar_one_or_none()
    if not vinculo:
        return {"paciente": None, "actividades_hoy": [], "seguimientos": [], "alertas": []}

    paciente_q = await db.execute(
        select(Paciente).where(Paciente.id == vinculo.paciente_id)
    )
    paciente = paciente_q.scalar_one_or_none()
    if not paciente:
        return {"paciente": None, "actividades_hoy": [], "seguimientos": [], "alertas": []}

    # ── Registros recientes para calcular bienestar y último registro ──────
    regs_q = await db.execute(
        select(RegistroSeguimiento)
        .options(joinedload(RegistroSeguimiento.autor))
        .where(RegistroSeguimiento.paciente_id == paciente.id)
        .order_by(RegistroSeguimiento.fecha_registro.desc())
        .limit(10)
    )
    regs = regs_q.scalars().all()

    bienestar = _bienestar_desde_registros(regs)
    ultimo_registro = regs[0].fecha_registro if regs else None

    # ── Equipo terapéutico ─────────────────────────────────────────────────
    equipos_q = await db.execute(
        select(EquipoTerapeutico)
        .options(joinedload(EquipoTerapeutico.miembros).joinedload(MiembroEquipo.terapeuta).joinedload(Terapeuta.usuario))
        .where(
            EquipoTerapeutico.paciente_id == paciente.id,
            EquipoTerapeutico.activo == True,
        )
    )
    equipos = equipos_q.scalars().all()
    equipo_list = []
    for eq in equipos:
        for m in eq.miembros:
            if m.activo and m.terapeuta and m.terapeuta.usuario:
                u = m.terapeuta.usuario
                equipo_list.append({
                    "id":       str(m.terapeuta_id),
                    "nombre":   f"{u.nombre} {u.apellido}",
                    "profesion": m.terapeuta.profesion or "",
                    "rol":      m.rol_en_equipo,
                    "av":       _initials(u.nombre, u.apellido),
                    "avClass":  _av_class(u.nombre or ""),
                })

    # ── Actividades del paciente con estado completado hoy ─────────────────
    inicio_hoy = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    acts_q = await db.execute(
        select(ActividadFamiliar)
        .where(
            ActividadFamiliar.paciente_id == paciente.id,
            ActividadFamiliar.activa == True,
        )
        .limit(5)
    )
    acts = acts_q.scalars().all()

    # IDs de actividades completadas hoy por este familiar
    if acts:
        act_ids = [a.id for a in acts]
        prog_q = await db.execute(
            select(ProgresoActividad.actividad_id)
            .where(
                ProgresoActividad.familiar_id == familiar.id,
                ProgresoActividad.actividad_id.in_(act_ids),
                ProgresoActividad.completada_en >= inicio_hoy,
            )
        )
        completadas_hoy = {row[0] for row in prog_q.all()}
    else:
        completadas_hoy = set()

    # ── Alertas activas del familiar ───────────────────────────────────────
    alertas_q = await db.execute(
        select(Alerta)
        .where(Alerta.resuelta == False)
        .order_by(Alerta.creada_en.desc())
        .limit(3)
    )
    alertas = alertas_q.scalars().all()

    return {
        "paciente": {
            "id":               str(paciente.id),
            "nombre":           paciente.nombre_enc or "Paciente",
            "apellido":         paciente.apellido_enc or "",
            "edad":             _calcular_edad(paciente.fecha_nacimiento),
            "diagnostico":      paciente.diagnostico.nombre if paciente.diagnostico else "",
            "nivel_soporte":    paciente.nivel_soporte,
            "bienestar":        bienestar,
            "bienestar_label":  _bienestar_label(bienestar),
            "ultimo_registro":  ultimo_registro.isoformat() if ultimo_registro else None,
            "equipo":           equipo_list,
        },
        "actividades_hoy": [
            {
                "id":          str(a.id),
                "titulo":      a.titulo,
                "descripcion": a.descripcion or "",
                "completada":  a.id in completadas_hoy,
                "frecuencia":  _frecuencia_label(a.frecuencia),
                "objetivo":    a.objetivo or "",
            }
            for a in acts
        ],
        "seguimientos": [
            {
                "id":      str(r.id),
                "autor":   f"{r.autor.nombre} {r.autor.apellido}" if r.autor else "Equipo",
                "av":      _initials(r.autor.nombre if r.autor else "E", r.autor.apellido if r.autor else ""),
                "avClass": _av_class(r.autor.nombre if r.autor else ""),
                "texto":   r.contenido_enc or "",
                "tipo":    r.tipo or "evolucion",
                "fecha":   r.fecha_registro.isoformat() if r.fecha_registro else None,
            }
            for r in regs[:3]
        ],
        "alertas": [
            {
                "id":    str(a.id),
                "texto": a.descripcion or "",
                "tipo":  a.tipo or "aviso",
                "fecha": a.creada_en.isoformat() if a.creada_en else None,
            }
            for a in alertas
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# FAMILIAR SEGUIMIENTOS  —  GET /api/v1/familiar/seguimientos
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/familiar/seguimientos", summary="Seguimientos del paciente del familiar")
async def familiar_seguimientos(current_user: CurrentUser, db: DBDep):
    familiar_q = await db.execute(
        select(Familiar).where(Familiar.usuario_id == current_user.id)
    )
    familiar = familiar_q.scalar_one_or_none()
    if not familiar:
        return []

    vinculo_q = await db.execute(
        select(VinculoPaciente)
        .where(VinculoPaciente.familiar_id == familiar.id, VinculoPaciente.activo == True)
        .limit(1)
    )
    vinculo = vinculo_q.scalar_one_or_none()
    if not vinculo:
        return []

    regs_q = await db.execute(
        select(RegistroSeguimiento)
        .options(joinedload(RegistroSeguimiento.autor))
        .where(RegistroSeguimiento.paciente_id == vinculo.paciente_id)
        .order_by(RegistroSeguimiento.fecha_registro.desc())
        .limit(30)
    )
    regs = regs_q.scalars().all()

    return [
        {
            "id":      str(r.id),
            "autor":   f"{r.autor.nombre} {r.autor.apellido}" if r.autor else "Equipo",
            "rol":     "Terapeuta",
            "av":      _initials(r.autor.nombre if r.autor else "E", r.autor.apellido if r.autor else ""),
            "avClass": _av_class(r.autor.nombre if r.autor else ""),
            "texto":   r.contenido_enc or "",
            "tipo":    r.tipo or "evolucion",
            "fecha":   r.fecha_registro.isoformat() if r.fecha_registro else None,
        }
        for r in regs
    ]


# ─────────────────────────────────────────────────────────────────────────────
# FAMILIAR ACTIVIDADES  —  GET /api/v1/familiar/actividades
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/familiar/actividades", summary="Actividades del paciente del familiar")
async def familiar_actividades(current_user: CurrentUser, db: DBDep):
    familiar_q = await db.execute(
        select(Familiar).where(Familiar.usuario_id == current_user.id)
    )
    familiar = familiar_q.scalar_one_or_none()
    if not familiar:
        return []

    vinculo_q = await db.execute(
        select(VinculoPaciente)
        .where(VinculoPaciente.familiar_id == familiar.id, VinculoPaciente.activo == True)
        .limit(1)
    )
    vinculo = vinculo_q.scalar_one_or_none()
    if not vinculo:
        return []

    acts_q = await db.execute(
        select(ActividadFamiliar)
        .where(
            ActividadFamiliar.paciente_id == vinculo.paciente_id,
            ActividadFamiliar.activa == True,
        )
        .order_by(ActividadFamiliar.creado_en.desc())
    )
    acts = acts_q.scalars().all()

    inicio_hoy = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    if acts:
        act_ids = [a.id for a in acts]

        # Todos los registros de progreso de este familiar para estas actividades
        prog_q = await db.execute(
            select(
                ProgresoActividad.actividad_id,
                ProgresoActividad.es_completada,
                ProgresoActividad.etapas_completadas,
                ProgresoActividad.completada_en,
            )
            .where(
                ProgresoActividad.familiar_id == familiar.id,
                ProgresoActividad.actividad_id.in_(act_ids),
            )
        )
        all_progs = prog_q.all()

        # Diccionario actividad_id → lista de sesiones
        from collections import defaultdict
        sesiones_por_act = defaultdict(list)
        completadas_hoy = set()
        for row in all_progs:
            sesiones_por_act[row.actividad_id].append(row)
            if row.completada_en >= inicio_hoy:
                completadas_hoy.add(row.actividad_id)
    else:
        sesiones_por_act = {}
        completadas_hoy = set()

    from datetime import date, timedelta

    def _tasa_cumplimiento(act, sesiones):
        """
        % de cumplimiento = etapas_efectivas_totales / etapas_esperadas_totales × 100
        etapas_efectivas = suma de (total_etapas si completada, else etapas_completadas) por sesión
        etapas_esperadas = total_etapas × completiones_esperadas_por_frecuencia
        """
        if not sesiones:
            return 0
        etapas_efectivas = sum(
            act.total_etapas if s.es_completada else (s.etapas_completadas or 0)
            for s in sesiones
        )
        dias = max(1, (date.today() - act.creado_en.date()).days) if act.creado_en else 1
        completiones_esperadas = {
            "diaria": dias, "semanal": max(1, dias // 7),
            "quincenal": max(1, dias // 15), "libre": max(1, dias // 7),
        }.get(act.frecuencia or "libre", max(1, dias // 7))
        etapas_esperadas = act.total_etapas * completiones_esperadas
        return min(100, round(etapas_efectivas / etapas_esperadas * 100))

    return [
        {
            "id":             str(a.id),
            "titulo":         a.titulo,
            "descripcion":    a.descripcion or "",
            "objetivo":       a.objetivo or "",
            "frecuencia":     _frecuencia_label(a.frecuencia),
            "total_etapas":   a.total_etapas,
            "completada":     a.id in completadas_hoy,
            "veces_realizadas": len(sesiones_por_act.get(a.id, [])),
            "tasa_cumplimiento": _tasa_cumplimiento(a, sesiones_por_act.get(a.id, [])),
            "creado_en":      a.creado_en.isoformat() if a.creado_en else None,
        }
        for a in acts
    ]


# ─────────────────────────────────────────────────────────────────────────────
# FAMILIAR ALERTAS  —  GET /api/v1/familiar/alertas
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/familiar/alertas", summary="Alertas del familiar")
async def familiar_alertas(current_user: CurrentUser, db: DBDep):
    alertas_q = await db.execute(
        select(Alerta)
        .where(Alerta.resuelta == False)
        .order_by(Alerta.creada_en.desc())
        .limit(20)
    )
    alertas = alertas_q.scalars().all()

    TIPO_LABEL = {"urgente": "Urgente", "aviso": "Aviso", "positivo": "Positivo", "incidente": "Incidente"}

    return [
        {
            "id":     str(a.id),
            "titulo": TIPO_LABEL.get(a.tipo, "Aviso"),
            "texto":  a.descripcion or "",
            "tipo":   a.tipo or "aviso",
            "fecha":  a.creada_en.isoformat() if a.creada_en else None,
            "leida":  False,
        }
        for a in alertas
    ]


# ─────────────────────────────────────────────────────────────────────────────
# TERAPEUTA INTERNO DASHBOARD  —  GET /api/v1/terapeuta/dashboard
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/terapeuta/dashboard", summary="Dashboard agregado para terapeuta interno")
async def terapeuta_dashboard(current_user: CurrentUser, db: DBDep):
    ahora = datetime.now(timezone.utc)
    hace_7_dias = ahora - timedelta(days=7)

    # Terapeuta del usuario actual
    ter_q = await db.execute(
        select(Terapeuta).where(Terapeuta.usuario_id == current_user.id)
    )
    terapeuta = ter_q.scalar_one_or_none()

    # Pacientes activos — si hay terapeuta, filtra por sus equipos
    if terapeuta:
        # Pacientes cuyos equipos incluyen a este terapeuta
        pacs_ids_q = await db.execute(
            select(EquipoTerapeutico.paciente_id)
            .join(MiembroEquipo, MiembroEquipo.equipo_id == EquipoTerapeutico.id)
            .where(
                MiembroEquipo.terapeuta_id == terapeuta.id,
                MiembroEquipo.activo == True,
                EquipoTerapeutico.activo == True,
            )
        )
        pac_ids = list({row[0] for row in pacs_ids_q.all()})

        if pac_ids:
            pacs_q = await db.execute(
                select(Paciente)
                .where(Paciente.id.in_(pac_ids), Paciente.activo == True)
                .limit(10)
            )
        else:
            pacs_q = await db.execute(
                select(Paciente).where(Paciente.activo == True).limit(10)
            )
    else:
        pacs_q = await db.execute(
            select(Paciente).where(Paciente.activo == True).limit(10)
        )
    pacs = pacs_q.scalars().all()

    # Último registro por paciente
    ultima_sesion_map = {}
    if pacs:
        for p in pacs:
            last_q = await db.execute(
                select(RegistroSeguimiento.fecha_registro)
                .where(RegistroSeguimiento.paciente_id == p.id)
                .order_by(RegistroSeguimiento.fecha_registro.desc())
                .limit(1)
            )
            last = last_q.scalar_one_or_none()
            ultima_sesion_map[p.id] = _formato_fecha_relativa(last)

    # Bienestar por paciente (últimos 5 registros)
    bienestar_map = {}
    if pacs:
        for p in pacs:
            regs_q = await db.execute(
                select(RegistroSeguimiento)
                .where(RegistroSeguimiento.paciente_id == p.id)
                .order_by(RegistroSeguimiento.fecha_registro.desc())
                .limit(5)
            )
            regs_p = regs_q.scalars().all()
            bienestar_map[p.id] = _bienestar_desde_registros(regs_p)

    # Alertas activas
    alertas_q = await db.execute(
        select(Alerta)
        .where(Alerta.resuelta == False)
        .order_by(Alerta.creada_en.desc())
        .limit(5)
    )
    alertas = alertas_q.scalars().all()

    # Nombres de pacientes para alertas
    pac_nombres = {str(p.id): p.nombre_enc or "Paciente" for p in pacs}

    # KPIs
    sesiones_semana = (await db.execute(
        select(func.count(RegistroSeguimiento.id))
        .where(RegistroSeguimiento.creado_en >= hace_7_dias)
    )).scalar() or 0

    actividades_total = (await db.execute(
        select(func.count(ActividadFamiliar.id))
        .where(ActividadFamiliar.activa == True)
    )).scalar() or 0

    return {
        "pacientes": [
            {
                "id":            str(p.id),
                "nombre":        p.nombre_enc or "Paciente",
                "apellido":      p.apellido_enc or "",
                "edad":          _calcular_edad(p.fecha_nacimiento),
                "diagnostico":   p.diagnostico.nombre if p.diagnostico else "",
                "nivel_soporte": p.nivel_soporte,
                "bienestar":     bienestar_map.get(p.id),
                "bienestar_label": _bienestar_label(bienestar_map.get(p.id)),
                "ultima_sesion": ultima_sesion_map.get(p.id),
                "av":            _initials(p.nombre_enc or "P"),
                "avClass":       _av_class(p.nombre_enc or ""),
            }
            for p in pacs
        ],
        "alertas": [
            {
                "id":       str(a.id),
                "paciente": pac_nombres.get(str(a.paciente_id), "Paciente") if hasattr(a, 'paciente_id') and a.paciente_id else "—",
                "texto":    a.descripcion or "",
                "tipo":     a.tipo or "incidente",
                "fecha":    a.creada_en.isoformat() if a.creada_en else None,
            }
            for a in alertas
        ],
        "kpis": {
            "pacientes":   len(pacs),
            "sesiones":    sesiones_semana,
            "alertas":     len(alertas),
            "actividades": actividades_total,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# TERAPEUTA EXTERNO DASHBOARD  —  GET /api/v1/terapeuta/externo/dashboard
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/terapeuta/externo/dashboard", summary="Dashboard para terapeuta externo")
async def terapeuta_externo_dashboard(current_user: CurrentUser, db: DBDep):
    # Terapeuta del usuario actual
    ter_q = await db.execute(
        select(Terapeuta).where(Terapeuta.usuario_id == current_user.id)
    )
    terapeuta = ter_q.scalar_one_or_none()

    # Pacientes asignados a este terapeuta externo
    if terapeuta:
        pacs_ids_q = await db.execute(
            select(EquipoTerapeutico.paciente_id)
            .join(MiembroEquipo, MiembroEquipo.equipo_id == EquipoTerapeutico.id)
            .where(
                MiembroEquipo.terapeuta_id == terapeuta.id,
                MiembroEquipo.activo == True,
                EquipoTerapeutico.activo == True,
            )
        )
        pac_ids = list({row[0] for row in pacs_ids_q.all()})

        if pac_ids:
            pacs_q = await db.execute(
                select(Paciente)
                .where(Paciente.id.in_(pac_ids), Paciente.activo == True)
                .limit(5)
            )
        else:
            pacs_q = await db.execute(
                select(Paciente).where(Paciente.activo == True).limit(5)
            )
    else:
        pacs_q = await db.execute(
            select(Paciente).where(Paciente.activo == True).limit(5)
        )
    pacs = pacs_q.scalars().all()

    # Último registro y cantidad de registros por paciente
    ultima_visita_map = {}
    registros_count_map = {}
    if pacs:
        for p in pacs:
            last_q = await db.execute(
                select(RegistroSeguimiento.fecha_registro)
                .where(RegistroSeguimiento.paciente_id == p.id)
                .order_by(RegistroSeguimiento.fecha_registro.desc())
                .limit(1)
            )
            ultima_visita_map[p.id] = _formato_fecha_relativa(last_q.scalar_one_or_none())

            count_q = await db.execute(
                select(func.count(RegistroSeguimiento.id))
                .where(RegistroSeguimiento.paciente_id == p.id)
            )
            registros_count_map[p.id] = count_q.scalar() or 0

    return {
        "pacientes": [
            {
                "id":           str(p.id),
                "nombre":       p.nombre_enc or "Paciente",
                "apellido":     p.apellido_enc or "",
                "edad":         _calcular_edad(p.fecha_nacimiento),
                "diagnostico":  p.diagnostico.nombre if p.diagnostico else "",
                "nivel_soporte": p.nivel_soporte,
                "ultima_visita": ultima_visita_map.get(p.id),
                "registros":    registros_count_map.get(p.id, 0),
                "av":           _initials(p.nombre_enc or "P"),
                "avClass":      _av_class(p.nombre_enc or ""),
            }
            for p in pacs
        ],
        "agenda": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# FAMILIAR: MIS VÍNCULOS — GET /api/v1/familiar/mis-vinculos
# Devuelve todos los pacientes a los que está vinculado el familiar logueado.
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/familiar/mis-vinculos",
    summary="Pacientes vinculados al familiar autenticado",
    dependencies=[Depends(require_roles("familia"))],
)
async def familiar_mis_vinculos(current_user: CurrentUser, db: DBDep):
    # Buscar perfil familiar
    fam_q = await db.execute(
        select(Familiar).where(Familiar.usuario_id == current_user.id)
    )
    familiar = fam_q.scalar_one_or_none()
    if not familiar:
        return []

    # Cargar todos los vínculos activos con paciente y parentesco
    v_q = await db.execute(
        select(VinculoPaciente)
        .options(
            joinedload(VinculoPaciente.paciente),
            joinedload(VinculoPaciente.parentesco),
        )
        .where(
            VinculoPaciente.familiar_id == familiar.id,
            VinculoPaciente.activo == True,
        )
        .order_by(VinculoPaciente.desde)
    )
    vinculos = v_q.unique().scalars().all()

    result = []
    for v in vinculos:
        p = v.paciente
        if not p:
            continue
        result.append({
            "vinculo_id":        str(v.id),
            "paciente_id":       str(p.id),
            "nombre":            p.nombre_enc or "—",
            "apellido":          p.apellido_enc or "",
            "edad":              _calcular_edad(p.fecha_nacimiento),
            "fecha_nacimiento":  p.fecha_nacimiento.isoformat() if p.fecha_nacimiento else None,
            "sexo":              p.sexo,
            "nivel_soporte":     p.nivel_soporte,
            "parentesco":        v.id_parentesco,
            "parentesco_nombre": v.parentesco.nombre if v.parentesco else v.id_parentesco,
            "es_tutor_legal":    v.es_tutor_legal,
            "autorizado_medico": v.autorizado_medico,
            "vinculado_desde":   v.desde.isoformat() if v.desde else None,
            "activo":            p.activo,
        })
    return result
