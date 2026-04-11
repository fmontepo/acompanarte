# app/api/auditoria_router.py
# Solo lectura — la auditoría nunca se crea desde la API
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.auditoria import EventoAuditoria
from app.schemas.auditoria import EventoAuditoriaRead
from app.api.deps import require_roles

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])

@router.get(
    "/",
    response_model=List[EventoAuditoriaRead],
    dependencies=[Depends(require_roles("admin"))],
    summary="Listar eventos de auditoría",
)
async def listar_auditoria(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    result = await db.execute(
        select(EventoAuditoria)
        .order_by(EventoAuditoria.timestamp.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()
