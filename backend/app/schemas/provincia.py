from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class ProvinciaBase(BaseModel):
    pass


class ProvinciaCreate(ProvinciaBase):
    pass


class ProvinciaRead(ProvinciaBase):
    id: Optional[UUID]
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
