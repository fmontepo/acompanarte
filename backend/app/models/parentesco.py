# app/models/parentesco.py
# Catálogo de tipos de parentesco — tabla de referencia
from sqlalchemy import Column, String
from app.db.base import Base


class Parentesco(Base):
    __tablename__ = "parentescos"

    id_parentesco = Column(String(2), primary_key=True, comment="Ej: MA=madre, PA=padre, AB=abuelo")
    nombre = Column(String, nullable=False)

    def __repr__(self):
        return f"<Parentesco {self.id_parentesco} - {self.nombre}>"
