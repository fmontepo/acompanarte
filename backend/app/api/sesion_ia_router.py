# app/api/sesion_ia_router.py
# Endpoints del módulo IA — el más crítico del sistema
# Implementa el contrato de API definido en la arquitectura:
#   POST /ia/consulta → pipeline RAG completo

from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.ia import SesionIA, MensajeIA
from app.schemas.sesion_ia import SesionIACreate, SesionIARead
from app.api.deps import CurrentUser, require_roles
from app.services.ia_service import procesar_consulta_ia

router = APIRouter(prefix="/ia", tags=["Inteligencia Artificial"])


# ---------------------------------------------------------------------------
# POST /api/v1/ia/sesion — iniciar nueva sesión IA
# ---------------------------------------------------------------------------
@router.post(
    "/sesion",
    response_model=SesionIARead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("familiar", "terapeuta", "admin"))],
    summary="Iniciar nueva sesión de consulta IA",
)
async def iniciar_sesion(
    data: SesionIACreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Obtener el familiar asociado al usuario
    from app.models.familiar import Familiar
    result = await db.execute(
        select(Familiar).where(Familiar.usuario_id == current_user.id)
    )
    familiar = result.scalar_one_or_none()

    if not familiar:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo familiares pueden iniciar sesiones de consulta IA"
        )

    sesion = SesionIA(
        id=uuid4(),
        familiar_id=familiar.id,
        paciente_id=data.paciente_id,
        estado="activa",
        contexto_anonimo=data.contexto_anonimo,
    )
    db.add(sesion)
    await db.commit()
    await db.refresh(sesion)
    return sesion


# ---------------------------------------------------------------------------
# POST /api/v1/ia/consulta — enviar consulta al asistente IA (pipeline RAG)
# ---------------------------------------------------------------------------
@router.post(
    "/consulta",
    summary="Enviar consulta al asistente IA",
)
async def consulta_ia(
    sesion_id: UUID,
    mensaje: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Verificar que la sesión existe y pertenece al usuario
    result = await db.execute(
        select(SesionIA).where(SesionIA.id == sesion_id)
    )
    sesion = result.scalar_one_or_none()

    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada"
        )

    if sesion.estado != "activa":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La sesión no está activa"
        )

    if not mensaje or not mensaje.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El mensaje no puede estar vacío"
        )

    # Ejecutar pipeline RAG completo
    resultado = await procesar_consulta_ia(
        db=db,
        sesion_id=sesion_id,
        familiar_id=sesion.familiar_id,
        mensaje=mensaje.strip(),
    )

    return resultado


# ---------------------------------------------------------------------------
# POST /api/v1/ia/sesion/{id}/cerrar — cerrar sesión
# ---------------------------------------------------------------------------
@router.post(
    "/sesion/{sesion_id}/cerrar",
    response_model=SesionIARead,
    summary="Cerrar sesión de consulta IA",
)
async def cerrar_sesion(
    sesion_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SesionIA).where(SesionIA.id == sesion_id)
    )
    sesion = result.scalar_one_or_none()

    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada"
        )

    sesion.estado = "cerrada"
    sesion.cerrada_en = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sesion)
    return sesion


# ---------------------------------------------------------------------------
# GET /api/v1/ia/sesion/{id}/mensajes — historial de mensajes
# ---------------------------------------------------------------------------
@router.get(
    "/sesion/{sesion_id}/mensajes",
    summary="Obtener historial de mensajes de una sesión",
)
async def historial_mensajes(
    sesion_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MensajeIA)
        .where(MensajeIA.sesion_id == sesion_id)
        .order_by(MensajeIA.enviado_en.asc())
    )
    return result.scalars().all()
