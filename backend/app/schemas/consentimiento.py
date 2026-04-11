# app/schemas/consentimiento.py
# Consentimiento informado — Ley 25.326 Art. 6
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ConsentimientoCreate(BaseModel):
    usuario_id: UUID
    version: str
    aceptado: bool = True
    ip_origen: Optional[str] = None
    user_agent: Optional[str] = None


class ConsentimientoRevocar(BaseModel):
    usuario_id: UUID
    version: str


class ConsentimientoRead(BaseModel):
    id: UUID
    usuario_id: UUID
    version: str
    aceptado: bool
    ip_origen: Optional[str] = None
    user_agent: Optional[str] = None
    revocado: bool
    revocado_en: Optional[datetime] = None
    aceptado_en: datetime

    model_config = {"from_attributes": True}
