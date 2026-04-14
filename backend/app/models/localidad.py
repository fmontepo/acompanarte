# app/models/localidad.py
# Tabla de referencia geográfica — clave primaria compuesta (CP + subCP)
# Se usa en Usuario para vincular domicilio a localidad argentina

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Localidad(Base):
    __tablename__ = "localidades"

    codigo_postal = Column(String(4), primary_key=True)
    sub_codigo_postal = Column(String(2), primary_key=True)

    nombre = Column(String, nullable=False)

    id_provincia = Column(
        String(2),
        ForeignKey("provincias.id_provincia"),
        nullable=False,
    )

    provincia = relationship("Provincia", lazy="selectin")

    def __repr__(self):
        return f"<Localidad {self.nombre} ({self.codigo_postal}-{self.sub_codigo_postal})>"
