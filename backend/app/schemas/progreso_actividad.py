# app/schemas/progreso_actividad.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any


class ProgresoActividadCreate(BaseModel):
    actividad_id: UUID
    observacion: Optional[str] = None
    nivel_satisfaccion: Optional[int] = None
    multimedia: Optional[List[Dict[str, Any]]] = None

    @field_validator("nivel_satisfaccion")
    @classmethod
    def validar_escala(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError("nivel_satisfaccion debe estar entre 1 y 5")
        return v


class ProgresoActividadRead(BaseModel):
    id: UUID
    actividad_id: UUID
    familiar_id: UUID
    observacion: Optional[str] = None
    nivel_satisfaccion: Optional[int] = None
    multimedia: Optional[List[Dict[str, Any]]] = None
    completada_en: datetime

    model_config = {"from_attributes": True}
