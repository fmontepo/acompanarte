# app/schemas/actividad_familiar.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

FRECUENCIAS = {"diaria", "semanal", "quincenal", "libre"}


class ActividadFamiliarCreate(BaseModel):
    paciente_id: UUID
    titulo: str
    descripcion: Optional[str] = None
    objetivo: Optional[str] = None
    frecuencia: str = "diaria"

    @field_validator("frecuencia")
    @classmethod
    def validar_frecuencia(cls, v):
        if v not in FRECUENCIAS:
            raise ValueError(f"Frecuencia inválida. Valores: {FRECUENCIAS}")
        return v

    @field_validator("titulo")
    @classmethod
    def no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El título no puede estar vacío")
        return v.strip()


class ActividadFamiliarUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    objetivo: Optional[str] = None
    frecuencia: Optional[str] = None
    activa: Optional[bool] = None


class ActividadFamiliarRead(BaseModel):
    id: UUID
    terapeuta_id: UUID
    paciente_id: UUID
    titulo: str
    descripcion: Optional[str] = None
    objetivo: Optional[str] = None
    frecuencia: str
    activa: bool
    creado_en: datetime
    actualizado_en: datetime

    model_config = {"from_attributes": True}
