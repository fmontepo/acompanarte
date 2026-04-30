# app/api/progreso_router.py
# Registro de progreso de actividades terapéuticas por el familiar.
#
# POST /progreso/                           → registrar sesión (completa o parcial)
# GET  /progreso/actividad/{actividad_id}   → historial de una actividad

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import CurrentUser, require_roles
from app.models.progresoActividad import ProgresoActividad
from app.models.actividadFamiliar import ActividadFamiliar
from app.models.familiar import Familiar

router = APIRouter(
    prefix="/progreso",
    tags=["Progreso de actividades"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProgresoCreate(BaseModel):
    actividad_id: UUID
    # True (default) = se completó toda la actividad en esta sesión
    # False          = avance parcial (solo algunas etapas)
    es_completada: bool = True
    # Cuántas etapas se hicieron. Obligatorio si es_completada=False.
    # Ignorado (se usa total_etapas de la actividad) si es_completada=True.
    etapas_completadas: Optional[int] = None
    observacion: Optional[str] = None
    nivel_satisfaccion: Optional[int] = None

    @field_validator("nivel_satisfaccion")
    @classmethod
    def validar_satisfaccion(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError("nivel_satisfaccion debe estar entre 1 y 5")
        return v

    @field_validator("etapas_completadas")
    @classmethod
    def validar_etapas(cls, v):
        if v is not None and v < 1:
            raise ValueError("etapas_completadas debe ser al menos 1")
        return v


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_familiar(db: AsyncSession, usuario_id) -> Familiar | None:
    q = await db.execute(select(Familiar).where(Familiar.usuario_id == usuario_id))
    return q.scalar_one_or_none()


# ── POST /progreso/ ───────────────────────────────────────────────────────────

@router.post(
    "",
    status_code=201,
    summary="Registrar progreso de una actividad",
    dependencies=[Depends(require_roles("familiar", "admin"))],
)
async def registrar_progreso(
    body: ProgresoCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Obtener el familiar autenticado
    familiar = await _get_familiar(db, current_user.id)
    if not familiar:
        raise HTTPException(403, detail="Solo familiares pueden registrar progreso")

    # Obtener la actividad para validar etapas
    act_q = await db.execute(
        select(ActividadFamiliar).where(ActividadFamiliar.id == body.actividad_id)
    )
    actividad = act_q.scalar_one_or_none()
    if not actividad:
        raise HTTPException(404, detail="Actividad no encontrada")
    if not actividad.activa:
        raise HTTPException(400, detail="La actividad ya no está activa")

    # Validar etapas parciales
    if not body.es_completada:
        if body.etapas_completadas is None:
            raise HTTPException(
                422,
                detail="etapas_completadas es obligatorio cuando es_completada=False"
            )
        if body.etapas_completadas > actividad.total_etapas:
            raise HTTPException(
                422,
                detail=(
                    f"etapas_completadas ({body.etapas_completadas}) no puede superar "
                    f"total_etapas ({actividad.total_etapas})"
                ),
            )

    progreso = ProgresoActividad(
        actividad_id=body.actividad_id,
        familiar_id=familiar.id,
        es_completada=body.es_completada,
        etapas_completadas=None if body.es_completada else body.etapas_completadas,
        observacion=body.observacion,
        nivel_satisfaccion=body.nivel_satisfaccion,
    )
    db.add(progreso)
    await db.commit()
    await db.refresh(progreso)

    etapas_efectivas = (
        actividad.total_etapas if body.es_completada else body.etapas_completadas
    )

    return {
        "id":                  str(progreso.id),
        "actividad_id":        str(progreso.actividad_id),
        "familiar_id":         str(progreso.familiar_id),
        "es_completada":       progreso.es_completada,
        "etapas_completadas":  progreso.etapas_completadas,
        "etapas_efectivas":    etapas_efectivas,
        "total_etapas":        actividad.total_etapas,
        "observacion":         progreso.observacion,
        "nivel_satisfaccion":  progreso.nivel_satisfaccion,
        "completada_en":       progreso.completada_en.isoformat(),
        "titulo_actividad":    actividad.titulo,
    }


# ── GET /progreso/actividad/{actividad_id} ────────────────────────────────────

@router.get(
    "/actividad/{actividad_id}",
    summary="Historial de progreso de una actividad",
    dependencies=[Depends(require_roles("familiar", "ter-int", "ter-ext", "admin"))],
)
async def historial_progreso(
    actividad_id: UUID,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(ProgresoActividad)
        .where(ProgresoActividad.actividad_id == actividad_id)
        .order_by(ProgresoActividad.completada_en.desc())
        .limit(limit)
    )
    progresos = result.scalars().all()

    return [
        {
            "id":                  str(p.id),
            "familiar_id":         str(p.familiar_id),
            "es_completada":       p.es_completada,
            "etapas_completadas":  p.etapas_completadas,
            "observacion":         p.observacion,
            "nivel_satisfaccion":  p.nivel_satisfaccion,
            "completada_en":       p.completada_en.isoformat(),
        }
        for p in progresos
    ]
