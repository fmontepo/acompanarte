# app/models/provincia.py
# Catálogo de provincias argentinas — tabla de referencia
from sqlalchemy import Column, String
from app.db.base import Base


class Provincia(Base):
    __tablename__ = "provincias"

    id_provincia = Column(String(2), primary_key=True, comment="Código INDEC de 2 dígitos")
    nombre = Column(String, nullable=False)

    def __repr__(self):
        return f"<Provincia {self.id_provincia} - {self.nombre}>"
