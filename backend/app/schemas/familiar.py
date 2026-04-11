from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class FamiliarBase(BaseModel):
    pass


class FamiliarCreate(FamiliarBase):
    pass


class FamiliarRead(FamiliarBase):
    id: Optional[UUID]
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
