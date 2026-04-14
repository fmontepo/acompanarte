# app/models/terapeuta.py
# Terapeuta — extiende Usuario con datos profesionales
# Solo terapeutas validados pueden: cargar recursos, validar bibliografía,
# acceder a datos clínicos de sus pacientes asignados y resolver alertas.

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Terapeuta(Base):
    __tablename__ = "terapeutas"

    # ------------------------------------------------------------------
    # Identificación
    # ------------------------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK al usuario base (1:1)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Datos profesionales
    # ------------------------------------------------------------------
    matricula = Column(
        String,
        unique=True,
        nullable=False,
        comment="Número de matrícula profesional — debe ser único"
    )
    profesion = Column(String, nullable=False, comment="Ej: Psicólogo, Fonoaudiólogo")
    especialidad = Column(String, comment="Ej: TEA, Neurodesarrollo")
    institucion = Column(String, comment="Institución de pertenencia")

    # tipo_acceso: institucional | independiente | supervisor
    tipo_acceso = Column(
        String(20),
        nullable=False,
        default="independiente",
        comment="institucional | independiente | supervisor"
    )

    # ------------------------------------------------------------------
    # Estado de validación
    # Un terapeuta debe ser validado por un admin antes de operar
    # validado=False por default — requiere aprobación explícita
    # ------------------------------------------------------------------
    validado = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="False hasta que un admin valide las credenciales"
    )
    institucional = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True si pertenece a la institución cliente"
    )
    activo = Column(Boolean, nullable=False, default=True)

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    creado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    validado_en = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp de validación por el admin"
    )
    actualizado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ------------------------------------------------------------------
    # Índices
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_terapeuta_validado_activo", "validado", "activo"),
    )

    # ------------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------------
    usuario = relationship("Usuario", lazy="selectin")
    equipos = relationship(
        "MiembroEquipo",
        back_populates="terapeuta",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Terapeuta matricula={self.matricula} validado={self.validado}>"
