# app/models/permisoSeguimiento.py
# Control granular de acceso a registros de seguimiento
# Principio de mínimo privilegio: sin permiso explícito, sin acceso

from sqlalchemy import Column, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class PermisoSeguimiento(Base):
    __tablename__ = "permisos_seguimiento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    registro_id = Column(
        UUID(as_uuid=True),
        ForeignKey("registros_seguimiento.id"),
        nullable=False,
        index=True,
    )
    terapeuta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("terapeutas.id"),
        nullable=False,
        index=True,
    )

    puede_ver = Column(Boolean, nullable=False, default=True)
    puede_editar = Column(Boolean, nullable=False, default=False)
    puede_eliminar = Column(Boolean, nullable=False, default=False)

    otorgado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    otorgado_por = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=True,
        comment="Quién otorgó el permiso"
    )

    registro = relationship("RegistroSeguimiento", back_populates="permisos", lazy="selectin")
    terapeuta = relationship("Terapeuta", lazy="selectin")

    def __repr__(self):
        return f"<PermisoSeguimiento ver={self.puede_ver} editar={self.puede_editar}>"
