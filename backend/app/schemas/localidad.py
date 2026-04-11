# app/schemas/localidad.py
from pydantic import BaseModel
from typing import Optional


class LocalidadRead(BaseModel):
    codigo_postal: str
    sub_codigo_postal: str
    nombre: str
    id_provincia: str

    model_config = {"from_attributes": True}
