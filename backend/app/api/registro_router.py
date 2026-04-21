# app/api/registro_router.py
# Registros de seguimiento — el autor_id se inyecta desde el usuario autenticado

from typing import List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.registroSeguimiento import RegistroSeguimiento
from app.schemas.registro_seguimiento import (
    RegistroSeguimientoCreate, RegistroSeguimientoRead,
)
from app.api.deps import CurrentUser, require_roles

router = APIRouter(prefix="/registros", tags=["Registros"])


# ---------------------------------------------------------------------------
# POST /api/v1/registros/ — crear registro (terapeuta interno o externo)
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=RegistroSeguimientoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
    summary="Crear registro de seguimiento",
)
async def crear_registro(
    data: RegistroSeguimientoCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    registro = RegistroSeguimiento(
        paciente_id=data.paciente_id,
        autor_id=current_user.id,        # siempre del usuario autenticado
        contenido_enc=data.contenido,    # en prod: cifrar AES-256 aquí
        visibilidad=data.visibilidad,
        tipo=data.tipo,
        fecha_registro=data.fecha_registro,
    )
    db.add(registro)
    await db.commit()
    await db.refresh(registro)
    return registro


# ---------------------------------------------------------------------------
# GET /api/v1/registros/ — listar registros
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[RegistroSeguimientoRead],
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
    summary="Listar registros de seguimiento",
)
async def listar_registros(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    result = await db.execute(
        select(RegistroSeguimiento)
        .order_by(RegistroSeguimiento.creado_en.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /api/v1/registros/{id}
# ---------------------------------------------------------------------------
@router.get(
    "/{registro_id}",
    response_model=RegistroSeguimientoRead,
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
    summary="Obtener registro por ID",
)
async def obtener_registro(
    registro_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RegistroSeguimiento).where(RegistroSeguimiento.id == registro_id)
    )
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")
    return reg
