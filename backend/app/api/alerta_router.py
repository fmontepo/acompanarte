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


def _alerta_dict(a: Alerta) -> dict:
    """Serializa una alerta enriquecida con nombre del paciente vía sesion→paciente."""
    pac = None
    if a.sesion and a.sesion.paciente:
        pac = a.sesion.paciente

    nombre_pac = ""
    if pac:
        nombre_pac = " ".join(filter(None, [pac.nombre_enc, pac.apellido_enc])) or "Paciente"

    return {
        "id":               str(a.id),
        "sesion_id":        str(a.sesion_id),
        "mensaje_id":       str(a.mensaje_id) if a.mensaje_id else None,
        "revisada_por":     str(a.revisada_por) if a.revisada_por else None,
        "tipo":             a.tipo,
        "severidad":        a.severidad,
        "descripcion":      a.descripcion,
        "resuelta":         a.resuelta,
        "nota_resolucion":  a.nota_resolucion,
        "creada_en":        a.creada_en.isoformat() if a.creada_en else None,
        "resuelta_en":      a.resuelta_en.isoformat() if a.resuelta_en else None,
        # Campos enriquecidos para el frontend
        "paciente":         nombre_pac or "Paciente",
        "paciente_id":      str(pac.id) if pac else None,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/alertas — listar alertas pendientes (terapeuta/admin)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
    summary="Listar alertas pendientes",
)
async def listar_alertas(
    db: AsyncSession = Depends(get_db),
    solo_pendientes: bool = True,
    skip: int = 0,
    limit: int = 50,
):
    # Alerta.sesion y SesionIA.paciente ya tienen lazy="selectin" en los modelos,
    # por lo que SQLAlchemy los carga automáticamente al acceder a ellos.
    query = select(Alerta).order_by(
        Alerta.severidad.desc(),
        Alerta.creada_en.asc(),
    )
    if solo_pendientes:
        query = query.where(Alerta.resuelta == False)

    result = await db.execute(query.offset(skip).limit(limit))
    alertas = result.scalars().all()
    return [_alerta_dict(a) for a in alertas]


# ---------------------------------------------------------------------------
# GET /api/v1/alertas/{id} — detalle de una alerta
# ---------------------------------------------------------------------------
@router.get(
    "/{alerta_id}",
    response_model=AlertaRead,
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
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
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
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
