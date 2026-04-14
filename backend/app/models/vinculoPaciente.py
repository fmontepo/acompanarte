# app/models/vinculoPaciente.py
# Vínculo entre familiar y paciente — con tipo de parentesco y permisos legales
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, String, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class VinculoPaciente(Base):
    __tablename__ = "vinculos_paciente"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    familiar_id = Column(
        UUID(as_uuid=True),
        ForeignKey("familiares.id"),
        nullable=False,
        index=True,
    )
    paciente_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pacientes.id"),
        nullable=False,
        index=True,
    )
    id_parentesco = Column(
        String(2),
        ForeignKey("parentescos.id_parentesco"),
        nullable=False,
    )

    # Permisos legales — determinan qué puede hacer el familiar
    es_tutor_legal = Column(Boolean, nullable=False, default=False)
    autorizado_medico = Column(Boolean, nullable=False, default=False)
    activo = Column(Boolean, nullable=False, default=True)

    desde = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    hasta = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_vinculo_familiar_paciente", "familiar_id", "paciente_id"),
    )

    familiar = relationship("Familiar", back_populates="vinculos", lazy="selectin")
    paciente = relationship("Paciente", back_populates="vinculos", lazy="selectin")
    parentesco = relationship("Parentesco", lazy="selectin")

    def __repr__(self):
        return f"<VinculoPaciente tutor={self.es_tutor_legal} activo={self.activo}>"
