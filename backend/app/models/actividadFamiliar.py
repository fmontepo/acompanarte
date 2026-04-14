# app/models/actividadFamiliar.py
# Actividades terapéuticas asignadas por el terapeuta para hacer en casa
# El familiar registra el progreso en ProgresoActividad

from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class ActividadFamiliar(Base):
    __tablename__ = "actividades_familiar"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    terapeuta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("terapeutas.id"),
        nullable=False,
        index=True,
    )
    paciente_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pacientes.id"),
        nullable=False,
        index=True,
    )

    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    objetivo = Column(Text, nullable=True, comment="Objetivo terapéutico de la actividad")

    # frecuencia: diaria | semanal | quincenal | libre
    frecuencia = Column(
        String(15),
        nullable=False,
        default="diaria",
        comment="diaria | semanal | quincenal | libre",
    )

    activa = Column(Boolean, nullable=False, default=True, index=True)

    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("idx_actividad_paciente_activa", "paciente_id", "activa"),
    )

    terapeuta = relationship("Terapeuta", lazy="selectin")
    paciente = relationship("Paciente", back_populates="actividades", lazy="selectin")
    progresos = relationship("ProgresoActividad", back_populates="actividad", lazy="dynamic")

    def __repr__(self):
        return f"<ActividadFamiliar titulo={self.titulo!r} activa={self.activa}>"
