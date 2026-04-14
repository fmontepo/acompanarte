# app/models/consentimiento.py
# Registro de consentimiento informado — Ley 25.326 Art. 6
# Inmutable: nunca modificar un registro existente.
# Para revocar: crear nuevo registro con aceptado=False, revocado=True.

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class Consentimiento(Base):
    __tablename__ = "consentimientos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )

    # Versión de los términos aceptados — permite rastrear cambios
    version = Column(String(20), nullable=False, comment="Ej: '1.0', '1.1'")
    aceptado = Column(Boolean, nullable=False, default=True)

    # Contexto técnico para auditoría legal
    ip_origen = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Revocación — nuevo registro, nunca modificar el anterior
    revocado = Column(Boolean, nullable=False, default=False)
    revocado_en = Column(DateTime(timezone=True), nullable=True)

    # Timestamp inmutable — lo pone el servidor
    aceptado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    __table_args__ = (
        Index("idx_consentimiento_usuario_version", "usuario_id", "version"),
    )

    usuario = relationship("Usuario", lazy="selectin")

    def __repr__(self):
        return f"<Consentimiento v={self.version} aceptado={self.aceptado} revocado={self.revocado}>"
