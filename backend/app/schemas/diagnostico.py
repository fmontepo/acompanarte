from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class DiagnosticoBase(BaseModel):
    pass


class DiagnosticoCreate(DiagnosticoBase):
    pass


class DiagnosticoRead(DiagnosticoBase):
    id: Optional[UUID]
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
