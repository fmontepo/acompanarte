# app/models/familiar.py
# Familiar — extiende Usuario con datos específicos del rol
# Un familiar puede estar vinculado a uno o más pacientes vía VinculoPaciente

from sqlalchemy import Column, DateTime, ForeignKey, Boolean, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Familiar(Base):
    __tablename__ = "familiares"

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
    # Datos específicos del familiar
    # ------------------------------------------------------------------
    contacto_emergencia = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True si es el contacto de emergencia principal"
    )

    # ------------------------------------------------------------------
    # Consentimiento informado — Ley 25.326 Art. 6
    # Versión versionada para rastrear cambios en los términos
    # ------------------------------------------------------------------
    consentimiento_otorgado = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True si otorgó consentimiento explícito"
    )
    consentimiento_en = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp del último consentimiento otorgado"
    )
    consentimiento_version = Column(
        String(20),
        nullable=True,
        comment="Versión de los términos aceptados, ej: '1.0', '1.1'"
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    creado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    actualizado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ------------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------------
    usuario = relationship("Usuario", lazy="selectin")
    vinculos = relationship(
        "VinculoPaciente",
        back_populates="familiar",
        lazy="selectin",
    )
    sesiones_ia = relationship(
        "SesionIA",
        back_populates="familiar",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Familiar usuario_id={self.usuario_id} consentimiento={self.consentimiento_otorgado}>"
