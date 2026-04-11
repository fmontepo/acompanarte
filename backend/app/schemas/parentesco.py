# app/schemas/parentesco.py
from pydantic import BaseModel


class ParentescoRead(BaseModel):
    id_parentesco: str
    nombre: str

    model_config = {"from_attributes": True}
