# app/schemas/auditoria.py
# Solo lectura — los registros de auditoría nunca se crean desde la API directamente
# Se crean internamente desde el middleware o los services
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class EventoAuditoriaRead(BaseModel):
    id: UUID
    usuario_id: Optional[UUID] = None
    accion: str
    recurso_tipo: str
    recurso_id: Optional[UUID] = None
    ip_origen: Optional[str] = None
    resultado: str
    metadata_extra: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class AuditoriaFiltros(BaseModel):
    """Parámetros de filtrado para consultas de auditoría."""
    usuario_id: Optional[UUID] = None
    accion: Optional[str] = None
    recurso_tipo: Optional[str] = None
    resultado: Optional[str] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
