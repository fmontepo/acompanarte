# app/models/administrador.py
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class Administrador(Base):
    __tablename__ = "administradores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # 1=operador, 2=supervisor, 3=superadmin
    nivel_acceso = Column(Integer, nullable=False, default=1)
    activo = Column(Boolean, nullable=False, default=True)

    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    usuario = relationship("Usuario", lazy="selectin")

    def __repr__(self):
        return f"<Administrador nivel={self.nivel_acceso}>"
