from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class AlertaBase(BaseModel):
    pass


class AlertaCreate(AlertaBase):
    pass


class AlertaRead(AlertaBase):
    id: Optional[UUID]
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
