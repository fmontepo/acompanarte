# app/schemas/recurso_profesional.py

from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

TIPOS_VALIDOS = {"pdf", "articulo", "guia", "protocolo"}


class RecursoCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    tipo: str
    url_storage: Optional[str] = None
    contenido_texto: Optional[str] = None   # Texto del recurso — genera el embedding RAG

    @field_validator("tipo")
    @classmethod
    def validar_tipo(cls, v: str) -> str:
        if v not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Valores: {TIPOS_VALIDOS}")
        return v

    @field_validator("titulo")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El título no puede estar vacío")
        return v.strip()


class RecursoRead(BaseModel):
    id: UUID
    titulo: str
    descripcion: Optional[str] = None
    tipo: str
    url_storage: Optional[str] = None
    contenido_texto: Optional[str] = None
    validado: bool
    activo: bool
    subido_por: UUID
    validado_por: Optional[UUID] = None
    subido_en: datetime
    validado_en: Optional[datetime] = None

    model_config = {"from_attributes": True}
