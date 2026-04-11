# app/schemas/miembro_equipo.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

ROLES_EQUIPO = {"coordinador", "tratante", "colaborador", "supervisor"}


class MiembroEquipoCreate(BaseModel):
    equipo_id: UUID
    terapeuta_id: UUID
    rol_en_equipo: str = "tratante"
    hasta: Optional[datetime] = None

    @field_validator("rol_en_equipo")
    @classmethod
    def validar_rol(cls, v):
        if v not in ROLES_EQUIPO:
            raise ValueError(f"Rol inválido. Valores: {ROLES_EQUIPO}")
        return v


class MiembroEquipoUpdate(BaseModel):
    rol_en_equipo: Optional[str] = None
    activo: Optional[bool] = None
    hasta: Optional[datetime] = None


class MiembroEquipoRead(BaseModel):
    id: UUID
    equipo_id: UUID
    terapeuta_id: UUID
    rol_en_equipo: str
    activo: bool
    asignado_en: datetime
    hasta: Optional[datetime] = None

    model_config = {"from_attributes": True}
