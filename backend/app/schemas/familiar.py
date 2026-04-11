# app/schemas/familiar.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional


class FamiliarCreate(BaseModel):
    usuario_id: UUID
    contacto_emergencia: bool = False
    consentimiento_otorgado: bool = False
    consentimiento_version: Optional[str] = None


class FamiliarUpdate(BaseModel):
    contacto_emergencia: Optional[bool] = None
    consentimiento_otorgado: Optional[bool] = None
    consentimiento_version: Optional[str] = None


class FamiliarRead(BaseModel):
    id: UUID
    usuario_id: UUID
    contacto_emergencia: bool
    consentimiento_otorgado: bool
    consentimiento_en: Optional[datetime] = None
    consentimiento_version: Optional[str] = None
    creado_en: datetime
    actualizado_en: datetime

    model_config = {"from_attributes": True}
