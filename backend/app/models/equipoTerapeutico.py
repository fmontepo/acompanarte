# app/models/equipoTerapeutico.py
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, String, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class EquipoTerapeutico(Base):
    __tablename__ = "equipos_terapeuticos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    paciente_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pacientes.id"),
        nullable=False,
        index=True,
    )

    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)

    activo = Column(Boolean, nullable=False, default=True, index=True)

    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_equipo_paciente_activo", "paciente_id", "activo"),
    )

    paciente = relationship("Paciente", lazy="selectin")
    miembros = relationship("MiembroEquipo", back_populates="equipo", lazy="selectin")

    def __repr__(self):
        return f"<EquipoTerapeutico nombre={self.nombre!r} activo={self.activo}>"
