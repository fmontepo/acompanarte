# app/api/alerta_router.py
# Gestión de alertas generadas por el módulo IA
# Solo terapeutas y admins pueden ver y resolver alertas
# Principio Human-in-the-loop: toda alerta requiere resolución humana explícita

from typing import List
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.alerta import Alerta
from app.schemas.alerta import AlertaRead, AlertaResolver
from app.api.deps import CurrentUser, require_roles

router = APIRouter(prefix="/alertas", tags=["Alertas"])


# ---------------------------------------------------------------------------
# GET /api/v1/alertas — listar alertas pendientes (terapeuta/admin)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[AlertaRead],
    dependencies=[Depends(require_roles("admin", "terapeuta"))],
    summary="Listar alertas pendientes",
)
async def listar_alertas(
    db: AsyncSession = Depends(get_db),
    solo_pendientes: bool = True,
    skip: int = 0,
    limit: int = 50,
):
    query = select(Alerta).order_by(
        Alerta.severidad.desc(),
        Alerta.creada_en.asc(),
    )
    if solo_pendientes:
        query = query.where(Alerta.resuelta == False)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /api/v1/alertas/{id} — detalle de una alerta
# ---------------------------------------------------------------------------
@router.get(
    "/{alerta_id}",
    response_model=AlertaRead,
    dependencies=[Depends(require_roles("admin", "terapeuta"))],
    summary="Obtener detalle de una alerta",
)
async def obtener_alerta(
    alerta_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alerta).where(Alerta.id == alerta_id)
    )
    alerta = result.scalar_one_or_none()
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    return alerta


# ---------------------------------------------------------------------------
# POST /api/v1/alertas/{id}/resolver — resolver una alerta (Human-in-the-loop)
# ---------------------------------------------------------------------------
@router.post(
    "/{alerta_id}/resolver",
    response_model=AlertaRead,
    dependencies=[Depends(require_roles("admin", "terapeuta"))],
    summary="Marcar alerta como resuelta",
)
async def resolver_alerta(
    alerta_id: UUID,
    data: AlertaResolver,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alerta).where(Alerta.id == alerta_id)
    )
    alerta = result.scalar_one_or_none()

    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )

    if alerta.resuelta:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La alerta ya fue resuelta"
        )

    alerta.resuelta = True
    alerta.resuelta_en = datetime.now(timezone.utc)
    alerta.revisada_por = current_user.id
    alerta.nota_resolucion = data.nota_resolucion

    await db.commit()
    await db.refresh(alerta)
    return alerta
