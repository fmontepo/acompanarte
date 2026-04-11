# app/schemas/permiso_seguimiento.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class PermisoSeguimientoCreate(BaseModel):
    registro_id: UUID
    terapeuta_id: UUID
    puede_ver: bool = True
    puede_editar: bool = False
    puede_eliminar: bool = False


class PermisoSeguimientoUpdate(BaseModel):
    puede_ver: Optional[bool] = None
    puede_editar: Optional[bool] = None
    puede_eliminar: Optional[bool] = None


class PermisoSeguimientoRead(BaseModel):
    id: UUID
    registro_id: UUID
    terapeuta_id: UUID
    puede_ver: bool
    puede_editar: bool
    puede_eliminar: bool
    otorgado_en: datetime
    otorgado_por: Optional[UUID] = None

    model_config = {"from_attributes": True}
