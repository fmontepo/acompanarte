# app/models/paciente.py
# Datos del paciente — nombre cifrado a nivel app (campo _enc)
# El nivel de soporte TEA solo puede ser ingresado por un terapeuta validado

from sqlalchemy import (
    Column, String, Integer, Boolean, Date,
    Text, DateTime, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    # ------------------------------------------------------------------
    # Identificación
    # ------------------------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nombre cifrado a nivel aplicación antes de persistir
    # Nunca almacenar texto plano — ver servicio de cifrado
    nombre_enc = Column(Text, nullable=False, comment="Nombre cifrado AES-256")
    apellido_enc = Column(Text, comment="Apellido cifrado AES-256")

    fecha_nacimiento = Column(Date)
    sexo = Column(String(1), comment="M | F | X")

    # ------------------------------------------------------------------
    # Datos clínicos — solo terapeutas pueden escribir estos campos
    # ------------------------------------------------------------------
    diagnostico_id = Column(
        UUID(as_uuid=True),
        ForeignKey("diagnosticos.id"),
        nullable=True,
        comment="FK al diagnóstico formal — solo terapeuta"
    )

    nivel_soporte = Column(
        Integer,
        nullable=True,
        comment="Nivel TEA: 1 | 2 | 3 — solo ingresado por terapeuta"
    )

    observaciones_enc = Column(
        Text,
        comment="Observaciones clínicas cifradas"
    )

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    activo = Column(Boolean, nullable=False, default=True)

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
    diagnostico = relationship("Diagnostico", lazy="selectin")
    vinculos = relationship("VinculoPaciente", back_populates="paciente", lazy="selectin")
    sesiones_ia = relationship("SesionIA", back_populates="paciente", lazy="dynamic")
    registros = relationship("RegistroSeguimiento", back_populates="paciente", lazy="dynamic")
    actividades = relationship("ActividadFamiliar", back_populates="paciente", lazy="dynamic")

    def __repr__(self):
        return f"<Paciente id={self.id} nivel_soporte={self.nivel_soporte}>"
