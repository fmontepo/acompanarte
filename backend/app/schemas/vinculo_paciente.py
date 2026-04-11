# app/schemas/vinculo_paciente.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class VinculoPacienteCreate(BaseModel):
    familiar_id: UUID
    paciente_id: UUID
    id_parentesco: str
    es_tutor_legal: bool = False
    autorizado_medico: bool = False


class VinculoPacienteUpdate(BaseModel):
    es_tutor_legal: Optional[bool] = None
    autorizado_medico: Optional[bool] = None
    activo: Optional[bool] = None
    hasta: Optional[datetime] = None


class VinculoPacienteRead(BaseModel):
    id: UUID
    familiar_id: UUID
    paciente_id: UUID
    id_parentesco: str
    es_tutor_legal: bool
    autorizado_medico: bool
    activo: bool
    desde: datetime
    hasta: Optional[datetime] = None

    model_config = {"from_attributes": True}
