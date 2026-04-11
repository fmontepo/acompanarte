# app/schemas/sesion_ia.py

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class SesionIACreate(BaseModel):
    paciente_id: Optional[UUID] = None
    contexto_anonimo: Optional[Dict[str, Any]] = None


class SesionIARead(BaseModel):
    id: UUID
    familiar_id: UUID
    paciente_id: Optional[UUID] = None
    estado: str
    contexto_anonimo: Optional[Dict[str, Any]] = None
    iniciada_en: datetime
    cerrada_en: Optional[datetime] = None

    model_config = {"from_attributes": True}
