from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class ParentescoBase(BaseModel):
    pass


class ParentescoCreate(ParentescoBase):
    pass


class ParentescoRead(ParentescoBase):
    id: Optional[UUID]
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
