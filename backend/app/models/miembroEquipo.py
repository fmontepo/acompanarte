# app/models/miembroEquipo.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class MiembroEquipo(Base):
    __tablename__ = "miembros_equipo"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    equipo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("equipos_terapeuticos.id"),
        nullable=False,
        index=True,
    )
    terapeuta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("terapeutas.id"),
        nullable=False,
        index=True,
    )

    # rol_en_equipo: coordinador | tratante | colaborador | supervisor
    rol_en_equipo = Column(
        String(20),
        nullable=False,
        default="tratante",
        comment="coordinador | tratante | colaborador | supervisor",
    )
    activo = Column(Boolean, nullable=False, default=True)

    asignado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    hasta = Column(DateTime(timezone=True), nullable=True, comment="NULL = sin fecha de fin")

    __table_args__ = (
        Index("idx_miembro_equipo_terapeuta", "equipo_id", "terapeuta_id"),
    )

    equipo = relationship("EquipoTerapeutico", back_populates="miembros", lazy="selectin")
    terapeuta = relationship("Terapeuta", back_populates="equipos", lazy="selectin")

    def __repr__(self):
        return f"<MiembroEquipo rol={self.rol_en_equipo} activo={self.activo}>"
