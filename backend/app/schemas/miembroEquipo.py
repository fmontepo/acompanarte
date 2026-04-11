from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class MiembroEquipoBase(BaseModel):
    pass


class MiembroEquipoCreate(MiembroEquipoBase):
    pass


class MiembroEquipoRead(MiembroEquipoBase):
    id: Optional[UUID]
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
