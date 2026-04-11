# app/schemas/paciente.py

from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import date, datetime
from typing import Optional


class PacienteCreate(BaseModel):
    # El nombre viene en texto plano — el service lo cifra antes de persistir
    nombre: str
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None

    @field_validator("sexo")
    @classmethod
    def validar_sexo(cls, v):
        if v and v not in {"M", "F", "X"}:
            raise ValueError("Sexo inválido. Valores: M | F | X")
        return v


class PacienteRead(BaseModel):
    id: UUID
    # El nombre viene cifrado desde la DB — el service lo descifra antes de retornar
    nombre_enc: str
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None
    nivel_soporte: Optional[int] = None
    activo: bool
    creado_en: datetime

    model_config = {"from_attributes": True}
