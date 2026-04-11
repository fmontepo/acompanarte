# app/schemas/alerta.py

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class AlertaRead(BaseModel):
    id: UUID
    sesion_id: UUID
    mensaje_id: Optional[UUID] = None
    revisada_por: Optional[UUID] = None
    tipo: str
    severidad: int
    descripcion: str
    resuelta: bool
    nota_resolucion: Optional[str] = None
    creada_en: datetime
    resuelta_en: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertaResolver(BaseModel):
    nota_resolucion: str
