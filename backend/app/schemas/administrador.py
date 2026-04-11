# app/schemas/administrador.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional


class AdministradorCreate(BaseModel):
    usuario_id: UUID
    nivel_acceso: int = 1

    @field_validator("nivel_acceso")
    @classmethod
    def validar_nivel(cls, v):
        if v not in (1, 2, 3):
            raise ValueError("nivel_acceso debe ser 1, 2 o 3")
        return v


class AdministradorUpdate(BaseModel):
    nivel_acceso: Optional[int] = None
    activo: Optional[bool] = None


class AdministradorRead(BaseModel):
    id: UUID
    usuario_id: UUID
    nivel_acceso: int
    activo: bool
    creado_en: datetime
    actualizado_en: datetime

    model_config = {"from_attributes": True}
