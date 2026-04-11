# app/schemas/mensaje_ia.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

EMISORES = {"usuario", "ia"}


class MensajeIARead(BaseModel):
    id: UUID
    sesion_id: UUID
    contenido: str
    emisor: str
    genera_alerta: bool
    fuentes_rag: Optional[List[Dict[str, Any]]] = None
    filtro_aplicado: bool
    enviado_en: datetime

    model_config = {"from_attributes": True}


class ConsultaIARequest(BaseModel):
    """Schema para el request de consulta al asistente IA."""
    sesion_id: UUID
    mensaje: str

    @field_validator("mensaje")
    @classmethod
    def no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El mensaje no puede estar vacío")
        if len(v) > 2000:
            raise ValueError("El mensaje no puede superar los 2000 caracteres")
        return v.strip()


class ConsultaIAResponse(BaseModel):
    """Schema para la respuesta del asistente IA."""
    respuesta: str
    alerta: bool
    fuentes: List[Dict[str, Any]]
    filtro_aplicado: bool
