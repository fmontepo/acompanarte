# app/schemas/terapeuta.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

TIPOS_ACCESO = {"independiente", "institucional", "supervisor"}


class TerapeutaCreate(BaseModel):
    usuario_id: UUID
    matricula: str
    profesion: str
    especialidad: Optional[str] = None
    institucion: Optional[str] = None
    tipo_acceso: str = "independiente"
    institucional: bool = False

    @field_validator("tipo_acceso")
    @classmethod
    def validar_tipo(cls, v: str) -> str:
        if v not in TIPOS_ACCESO:
            raise ValueError(f"tipo_acceso inválido. Valores: {TIPOS_ACCESO}")
        return v

    @field_validator("matricula", "profesion")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v.strip()


class TerapeutaUpdate(BaseModel):
    profesion: Optional[str] = None
    especialidad: Optional[str] = None
    institucion: Optional[str] = None
    tipo_acceso: Optional[str] = None


class TerapeutaRead(BaseModel):
    id: UUID
    usuario_id: UUID
    matricula: str
    profesion: str
    especialidad: Optional[str] = None
    institucion: Optional[str] = None
    tipo_acceso: str
    validado: bool
    institucional: bool
    activo: bool
    creado_en: datetime
    validado_en: Optional[datetime] = None

    model_config = {"from_attributes": True}
