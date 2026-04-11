# app/schemas/registro_seguimiento.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import date, datetime
from typing import Optional

VISIBILIDADES = {"equipo", "terapeuta_principal", "todos"}
TIPOS = {"evolucion", "observacion", "incidente", "objetivo", "logro"}


class RegistroSeguimientoCreate(BaseModel):
    paciente_id: UUID
    # contenido viene en texto plano — el service lo cifra antes de persistir
    contenido: str
    visibilidad: str = "equipo"
    tipo: str = "evolucion"
    fecha_registro: date

    @field_validator("visibilidad")
    @classmethod
    def validar_visibilidad(cls, v):
        if v not in VISIBILIDADES:
            raise ValueError(f"Visibilidad inválida. Valores: {VISIBILIDADES}")
        return v

    @field_validator("tipo")
    @classmethod
    def validar_tipo(cls, v):
        if v not in TIPOS:
            raise ValueError(f"Tipo inválido. Valores: {TIPOS}")
        return v

    @field_validator("contenido")
    @classmethod
    def no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El contenido no puede estar vacío")
        return v.strip()


class RegistroSeguimientoUpdate(BaseModel):
    contenido: Optional[str] = None
    visibilidad: Optional[str] = None
    tipo: Optional[str] = None


class RegistroSeguimientoRead(BaseModel):
    id: UUID
    paciente_id: UUID
    autor_id: UUID
    # contenido_enc se retorna cifrado — el cliente lo descifra si tiene permiso
    contenido_enc: str
    visibilidad: str
    tipo: str
    fecha_registro: date
    version: int
    creado_en: datetime
    modificado_en: datetime

    model_config = {"from_attributes": True}
