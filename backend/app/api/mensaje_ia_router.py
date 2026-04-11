from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.ia import MensajeIA
from app.schemas.mensaje_ia import MensajeIARead
from app.api.deps import get_current_user

router = APIRouter(prefix="/mensajes-ia", tags=["Mensajes IA"])

@router.get("/{sesion_id}", response_model=List[MensajeIARead])
async def listar_mensajes(
    sesion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(MensajeIA)
        .where(MensajeIA.sesion_id == sesion_id)
        .order_by(MensajeIA.enviado_en.asc())
    )
    return result.scalars().all()
