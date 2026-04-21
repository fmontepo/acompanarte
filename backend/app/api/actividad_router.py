# app/api/actividad_router.py
# Actividades familiares — terapeuta_id se inyecta desde el usuario autenticado

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.actividadFamiliar import ActividadFamiliar
from app.models.terapeuta import Terapeuta
from app.schemas.actividad_familiar import ActividadFamiliarCreate, ActividadFamiliarRead
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
