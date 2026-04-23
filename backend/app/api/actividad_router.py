# app/api/actividad_router.py
# Actividades familiares — terapeuta_id se inyecta desde el usuario autenticado

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.actividadFamiliar import ActividadFamiliar
from app.models.paciente import Paciente
from app.models.terapeuta import Terapeuta
from app.schemas.actividad_familiar import (
    ActividadFamiliarCreate,
    ActividadFamiliarRead,
    ActividadFamiliarUpdate,
)
from app.api.deps import CurrentUser, require_roles

router = APIRouter(prefix="/actividades", tags=["Actividades"])


# ---------------------------------------------------------------------------
# POST /api/v1/actividades/ — crear actividad (solo terapeutas)
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=ActividadFamiliarRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
    summary="Crear actividad terapéutica",
)
async def crear_actividad(
    data: ActividadFamiliarCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Validar que el paciente existe
    if data.paciente_id:
        pac_q = await db.execute(
            select(Paciente).where(Paciente.id == data.paciente_id)
        )
        if pac_q.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente {data.paciente_id} no encontrado.",
            )

    # Buscar el registro Terapeuta asociado al usuario
    ter_q = await db.execute(
        select(Terapeuta).where(Terapeuta.usuario_id == current_user.id)
    )
    terapeuta = ter_q.scalar_one_or_none()

    actividad = ActividadFamiliar(
        terapeuta_id=terapeuta.id if terapeuta else current_user.id,
        paciente_id=data.paciente_id,
        titulo=data.titulo,
        descripcion=data.descripcion,
        objetivo=data.objetivo,
        frecuencia=data.frecuencia,
        total_etapas=data.total_etapas,
        activa=True,
    )
    db.add(actividad)
    await db.commit()
    await db.refresh(actividad)
    return actividad


# ---------------------------------------------------------------------------
# GET /api/v1/actividades/ — listar actividades
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[ActividadFamiliarRead],
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
    summary="Listar actividades",
)
async def listar_actividades(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    result = await db.execute(
        select(ActividadFamiliar)
        .where(ActividadFamiliar.activa == True)
        .order_by(ActividadFamiliar.creado_en.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /api/v1/actividades/{id}
# ---------------------------------------------------------------------------
@router.get(
    "/{actividad_id}",
    response_model=ActividadFamiliarRead,
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
)
async def obtener_actividad(actividad_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ActividadFamiliar).where(ActividadFamiliar.id == actividad_id)
    )
    act = result.scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return act


# ---------------------------------------------------------------------------
# PATCH /api/v1/actividades/{id} — editar o desactivar actividad
# ---------------------------------------------------------------------------
@router.patch(
    "/{actividad_id}",
    response_model=ActividadFamiliarRead,
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
    summary="Editar o desactivar una actividad",
)
async def editar_actividad(
    actividad_id: UUID,
    data: ActividadFamiliarUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ActividadFamiliar).where(ActividadFamiliar.id == actividad_id)
    )
    act = result.scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    if data.titulo is not None:
        act.titulo = data.titulo.strip()
    if data.descripcion is not None:
        act.descripcion = data.descripcion
    if data.objetivo is not None:
        act.objetivo = data.objetivo
    if data.frecuencia is not None:
        act.frecuencia = data.frecuencia
    if data.total_etapas is not None:
        if data.total_etapas < 1:
            raise HTTPException(422, detail="total_etapas debe ser al menos 1")
        act.total_etapas = data.total_etapas
    if data.activa is not None:
        act.activa = data.activa

    await db.commit()
    await db.refresh(act)
    return act
