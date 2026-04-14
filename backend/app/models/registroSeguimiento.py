# app/models/registroSeguimiento.py
# Registro clínico de seguimiento — contenido cifrado (PII)
# Solo terapeutas del equipo pueden crear y ver registros
# versión: permite historial de ediciones sin borrar datos anteriores

from sqlalchemy import Column, String, Integer, Date, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class RegistroSeguimiento(Base):
    __tablename__ = "registros_seguimiento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    paciente_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pacientes.id"),
        nullable=False,
        index=True,
    )
    autor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )

    # Contenido cifrado a nivel aplicación — AES-256
    contenido_enc = Column(Text, nullable=False, comment="Contenido cifrado AES-256")

    # visibilidad: equipo | terapeuta_principal | todos
    visibilidad = Column(
        String(25),
        nullable=False,
        default="equipo",
        comment="equipo | terapeuta_principal | todos",
    )

    # tipo: evolucion | observacion | incidente | objetivo | logro
    tipo = Column(
        String(20),
        nullable=False,
        default="evolucion",
        comment="evolucion | observacion | incidente | objetivo | logro",
    )

    fecha_registro = Column(Date, nullable=False)

    # Versionado — incrementa en cada edición; permite historial
    version = Column(Integer, nullable=False, default=1)

    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    modificado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("idx_registro_paciente_fecha", "paciente_id", "fecha_registro"),
        Index("idx_registro_autor", "autor_id"),
    )

    paciente = relationship("Paciente", back_populates="registros", lazy="selectin")
    autor = relationship("Usuario", lazy="selectin")
    permisos = relationship("PermisoSeguimiento", back_populates="registro", lazy="selectin")

    def __repr__(self):
        return f"<RegistroSeguimiento tipo={self.tipo} v={self.version}>"
