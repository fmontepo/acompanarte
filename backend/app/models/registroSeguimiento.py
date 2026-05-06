# app/models/registroSeguimiento.py
# Registro clínico de seguimiento — contenido cifrado (PII)
# Solo terapeutas del equipo pueden crear y ver registros
# versión: permite historial de ediciones sin borrar datos anteriores

from sqlalchemy import Column, String, Integer, Date, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from app.db.base import Base

EMBEDDING_DIM = 384


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

    # ── Embedding RAG clínico ────────────────────────────────────────────────
    # Generado por el batch scheduler sobre tipo + fecha + contenido_enc
    embedding = Column(
        Vector(EMBEDDING_DIM),
        nullable=True,
        comment=f"Vector {EMBEDDING_DIM}d para RAG clínico interno",
    )
    # Hash SHA-256 del texto embedeado — detecta cambios sin comparar timestamps
    embedding_hash = Column(
        String(64),
        nullable=True,
        comment="SHA-256 del texto fuente; permite skip si no hubo cambios",
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
