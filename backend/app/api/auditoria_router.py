# app/api/auditoria_router.py
# Solo lectura — la auditoría nunca se crea desde la API
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models.auditoria import EventoAuditoria
from app.models.usuario import Usuario
from app.api.deps import require_roles

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


class EventoAuditoriaEnriquecido(BaseModel):
    """Schema enriquecido con datos del usuario para el frontend."""
    id: UUID
    usuario_id: Optional[UUID] = None
    usuario: Optional[str] = None          # nombre + apellido
    rol: Optional[str] = None              # rol_key del usuario
    accion: str
    tipo: str                              # alias de recurso_tipo
    desc: str                              # alias de accion legible
    recurso_tipo: str
    recurso_id: Optional[UUID] = None
    ip: Optional[str] = None              # alias de ip_origen
    ip_origen: Optional[str] = None
    resultado: str
    metadata_extra: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


@router.get(
    "/",
    response_model=List[EventoAuditoriaEnriquecido],
    dependencies=[Depends(require_roles("admin"))],
    summary="Listar eventos de auditoría (enriquecidos con datos de usuario)",
)
async def listar_auditoria(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    # Obtener eventos
    result = await db.execute(
        select(EventoAuditoria)
        .order_by(EventoAuditoria.timestamp.desc())
        .offset(skip).limit(limit)
    )
    eventos = result.scalars().all()

    if not eventos:
        return []

    # Cargar usuarios únicos en un solo query
    user_ids = {e.usuario_id for e in eventos if e.usuario_id}
    usuarios_map: Dict[UUID, Usuario] = {}
    if user_ids:
        usuarios_q = await db.execute(
            select(Usuario)
            .options(joinedload(Usuario.rol))
            .where(Usuario.id.in_(user_ids))
        )
        for u in usuarios_q.scalars().all():
            usuarios_map[u.id] = u

    # Construir respuesta enriquecida
    enriched = []
    for e in eventos:
        usuario_obj = usuarios_map.get(e.usuario_id) if e.usuario_id else None
        nombre = f"{usuario_obj.nombre} {usuario_obj.apellido}" if usuario_obj else "Sistema"
        rol_key = usuario_obj.rol.key if usuario_obj and usuario_obj.rol else "sistema"

        enriched.append(EventoAuditoriaEnriquecido(
            id=e.id,
            usuario_id=e.usuario_id,
            usuario=nombre,
            rol=rol_key,
            accion=e.accion,
            tipo=e.recurso_tipo,
            desc=_desc_legible(e.accion, e.recurso_tipo),
            recurso_tipo=e.recurso_tipo,
            recurso_id=e.recurso_id,
            ip=e.ip_origen,
            ip_origen=e.ip_origen,
            resultado=e.resultado,
            metadata_extra=e.metadata_extra,
            timestamp=e.timestamp,
        ))

    return enriched


def _desc_legible(accion: str, recurso_tipo: str) -> str:
    """Genera una descripción legible para el log de auditoría."""
    ACCIONES = {
        "login":    "Inicio de sesión",
        "logout":   "Cierre de sesión",
        "create":   f"Creó {recurso_tipo}",
        "update":   f"Actualizó {recurso_tipo}",
        "delete":   f"Eliminó {recurso_tipo}",
        "view":     f"Consultó {recurso_tipo}",
        "export":   "Exportó datos",
        "register": "Registro de usuario",
    }
    return ACCIONES.get(accion.lower(), accion)
