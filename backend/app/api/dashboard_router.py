# app/api/dashboard_router.py
# Endpoints de agregación para los dashboards de cada rol.
# Cada endpoint consulta la DB y devuelve datos listos para el frontend.
# Si la DB está vacía devuelve estructuras vacías → el frontend usa MOCK.

from typing import Annotated
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from fastapi import Depends
from app.db.session import get_db
from app.api.deps import CurrentUser
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

router = APIRouter(tags=["Dashboards"])

DBDep = Annotated[AsyncSession, Depends(get_db)]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _av_class(nombre: str) -> str:
    COLORS = ["av-tl", "av-pp", "av-bu", "av-am", "av-rd"]
    idx = sum(ord(c) for c in (nombre or "")) % len(COLORS)
    return COLORS[idx]


def _initials(nombre: str, apellido: str) -> str:
    n = (nombre or "")[:1].upper()
    a = (apellido or "")[:1].upper()
    return f"{n}{a}" or "?"


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN DASHBOARD  —  GET /api/v1/admin/dashboard
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/admin/dashboard", summary="Dashboard agregado para administración")
async def admin_dashboard(current_user: CurrentUser, db: DBDep):
    # Total usuarios
    total_usuarios = (await db.execute(select(func.count(Usuario.id)))).scalar() or 0

    # Usuarios por rol
    rol_counts_q = await db.execute(
        select(Rol.key, func.count(Usuario.id))
        .join(Usuario, Usuario.rol_id == Rol.id)
        .group_by(Rol.key)
    )
    rol_counts = {row[0]: row[1] for row in rol_counts_q.all()}

    # Total pacientes
    total_pacientes = (await db.execute(select(func.count(Paciente.id)))).scalar() or 0

    # Usuarios recientes (últimos 5)
    recientes_q = await db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .order_by(Usuario.creado_en.desc())
        .limit(5)
    )
    recientes = recientes_q.scalars().all()

    return {
        "stats": {
            "usuarios": {
                "total": total_usuarios,
                "nuevos_mes": 0,   # requiere filtro por fecha
            },
            "pacientes": {
                "total": total_pacientes,
                "activos": total_pacientes,
                "alta_este_mes": 0,
            },
            "terapeutas": {
                "total": rol_counts.get("ter-int", 0) + rol_counts.get("ter-ext", 0),
                "internos": rol_counts.get("ter-int", 0),
                "externos": rol_counts.get("ter-ext", 0),
            },
            "actividades_hoy": 0,
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
    }


# ─────────────────────────────────────────────────────────────────────────────
# FAMILIAR DASHBOARD  —  GET /api/v1/familiar/dashboard
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/familiar/dashboard", summary="Dashboard agregado para familiar")
async def familiar_dashboard(current_user: CurrentUser, db: DBDep):
    # Buscar el registro de familiar del usuario actual
    familiar_q = await db.execute(
        select(Familiar).where(Familiar.usuario_id == current_user.id)
    )
    familiar = familiar_q.scalar_one_or_none()
    if not familiar:
        return {"paciente": None, "actividades_hoy": [], "seguimientos": [], "alertas": [], "equipo": []}

    # Paciente vinculado
    vinculo_q = await db.execute(
        select(VinculoPaciente)
        .where(VinculoPaciente.familiar_id == familiar.id, VinculoPaciente.activo == True)
        .limit(1)
    )
    vinculo = vinculo_q.scalar_one_or_none()
    if not vinculo:
        return {"paciente": None, "actividades_hoy": [], "seguimientos": [], "alertas": [], "equipo": []}

    paciente_q = await db.execute(select(Paciente).where(Paciente.id == vinculo.paciente_id))
    paciente = paciente_q.scalar_one_or_none()
    if not paciente:
        return {"paciente": None, "actividades_hoy": [], "seguimientos": [], "alertas": [], "equipo": []}

    # Actividades del paciente
    acts_q = await db.execute(
        select(ActividadFamiliar)
        .where(ActividadFamiliar.paciente_id == paciente.id, ActividadFamiliar.activa == True)
        .limit(4)
    )
    acts = acts_q.scalars().all()

    # Registros de seguimiento recientes
    regs_q = await db.execute(
        select(RegistroSeguimiento)
        .where(RegistroSeguimiento.paciente_id == paciente.id)
        .order_by(RegistroSeguimiento.fecha_registro.desc())
        .limit(3)
    )
    regs = regs_q.scalars().all()

    return {
        "paciente": {
            "id":          str(paciente.id),
            "nombre":      paciente.nombre_enc or "Paciente",
            "apellido":    "",
            "edad":        None,
            "diagnostico": paciente.diagnostico or "",
            "bienestar":   72,
            "bienestar_label": "Estable",
            "ultimo_registro": None,
            "equipo": [],
        },
        "actividades_hoy": [
            {
                "id":        str(a.id),
                "titulo":    a.titulo,
                "completada": False,
                "hora":      "08:30",
                "categoria": "Bienestar",
            }
            for a in acts
        ],
        "seguimientos": [
            {
                "id":    str(r.id),
                "autor": "Equipo",
                "rol":   "Terapeuta",
                "av":    "ET",
                "avClass": "av-tl",
                "texto": r.contenido_enc or "",
                "tipo":  r.tipo or "neutral",
                "fecha": r.fecha_registro.isoformat() if r.fecha_registro else None,
            }
            for r in regs
        ],
        "alertas": [],
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
            "autor":   getattr(r, "autor_nombre", "Terapeuta"),
            "rol":     "Terapeuta",
            "av":      "ET",
            "avClass": "av-tl",
            "texto":   r.contenido_enc or "",
            "tipo":    r.tipo or "neutral",
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
        .where(ActividadFamiliar.paciente_id == vinculo.paciente_id, ActividadFamiliar.activa == True)
        .order_by(ActividadFamiliar.creado_en.desc())
    )
    acts = acts_q.scalars().all()

    return [
        {
            "id":          str(a.id),
            "titulo":      a.titulo,
            "descripcion": a.descripcion or "",
            "completada":  False,
            "hora":        "08:30",
            "categoria":   "Bienestar",
            "color":       "var(--teal)",
            "bg":          "var(--teal2)",
            "progreso":    0,
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

    TIPO_LABEL = {"urgente": "Urgente", "aviso": "Aviso", "positivo": "Positivo"}

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
    from datetime import datetime, timezone, timedelta

    # Pacientes activos
    pacs_q = await db.execute(
        select(Paciente).where(Paciente.activo == True).limit(10)
    )
    pacs = pacs_q.scalars().all()

    # Alertas activas
    alertas_q = await db.execute(
        select(Alerta).where(Alerta.resuelta == False).order_by(Alerta.creada_en.desc()).limit(5)
    )
    alertas = alertas_q.scalars().all()

    # KPI: sesiones esta semana (registros creados en los últimos 7 días)
    hace_7_dias = datetime.now(timezone.utc) - timedelta(days=7)
    sesiones_q = await db.execute(
        select(func.count(RegistroSeguimiento.id))
        .where(RegistroSeguimiento.creado_en >= hace_7_dias)
    )
    sesiones_semana = sesiones_q.scalar() or 0

    # KPI: actividades asignadas (activas en la BD)
    acts_total_q = await db.execute(
        select(func.count(ActividadFamiliar.id))
        .where(ActividadFamiliar.activa == True)
    )
    actividades_total = acts_total_q.scalar() or 0

    return {
        "pacientes": [
            {
                "id":          str(p.id),
                "nombre":      p.nombre_enc or "Paciente",
                "edad":        None,
                "diagnostico": p.observaciones_enc or "",
                "bienestar":   70,
                "ultima_sesion": "Hoy",
                "proxima":     "Mañana",
                "av":          (p.nombre_enc or "P")[:2].upper(),
                "avClass":     _av_class(p.nombre_enc or ""),
            }
            for p in pacs
        ],
        "alertas": [
            {
                "id":       str(a.id),
                "paciente": "Paciente",
                "texto":    a.descripcion or "",
                "tipo":     a.tipo or "incidente",
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
    pacs_q = await db.execute(
        select(Paciente).where(Paciente.activo == True).limit(5)
    )
    pacs = pacs_q.scalars().all()

    return {
        "pacientes": [
            {
                "id":          str(p.id),
                "nombre":      p.nombre_enc or "Paciente",
                "edad":        None,
                "diagnostico": p.observaciones_enc or "",
                "ultima_visita": "hace 5 días",
                "proxima":     "Jue 10:00",
                "av":          (p.nombre_enc or "P")[:2].upper(),
                "avClass":     _av_class(p.nombre_enc or ""),
                "registros":   0,
            }
            for p in pacs
        ],
        "agenda": [],
    }
