# app/schemas/diagnostico.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional


class DiagnosticoCreate(BaseModel):
    codigo: Optional[str] = None
    nombre: str
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class DiagnosticoRead(BaseModel):
    id: UUID
    codigo: Optional[str] = None
    nombre: str
    descripcion: Optional[str] = None
    activo: bool

    model_config = {"from_attributes": True}
