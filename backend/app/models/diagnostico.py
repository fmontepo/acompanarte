# app/models/diagnostico.py
# Catálogo de diagnósticos — tabla de referencia, solo lectura para la app
# Solo administradores pueden agregar diagnósticos al catálogo

from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Diagnostico(Base):
    __tablename__ = "diagnosticos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Código CIE-11 o DSM-5
    codigo = Column(String(20), unique=True, nullable=True, comment="Código CIE-11 / DSM-5")
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)

    # Solo diagnósticos activos aparecen en el sistema
    activo = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Diagnostico codigo={self.codigo} nombre={self.nombre!r}>"
