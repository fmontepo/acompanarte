# app/schemas/equipo_terapeutico.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional


class EquipoTerapeuticoCreate(BaseModel):
    paciente_id: UUID
    nombre: str
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class EquipoTerapeuticoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class EquipoTerapeuticoRead(BaseModel):
    id: UUID
    paciente_id: UUID
    nombre: str
    descripcion: Optional[str] = None
    activo: bool
    creado_en: datetime
    actualizado_en: datetime

    model_config = {"from_attributes": True}
