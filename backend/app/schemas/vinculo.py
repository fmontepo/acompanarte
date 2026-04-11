from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class VinculoBase(BaseModel):
    pass


class VinculoCreate(VinculoBase):
    pass


class VinculoRead(VinculoBase):
    id: Optional[UUID]
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
