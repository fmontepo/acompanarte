# app/schemas/provincia.py
from pydantic import BaseModel


class ProvinciaRead(BaseModel):
    id_provincia: str
    nombre: str

    model_config = {"from_attributes": True}
