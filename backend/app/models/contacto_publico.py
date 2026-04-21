# app/models/contacto_publico.py
# Solicitudes de contacto generadas desde el Asistente IA público
# Se crea cuando un usuario anónimo acepta ser contactado por un terapeuta
# tras detectar una señal de alerta en la conversación.

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class ContactoPublico(Base):
    __tablename__ = "contactos_publicos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Datos del usuario anónimo
    nombre    = Column(String(200), nullable=False)
    celular   = Column(String(50),  nullable=True)
    mail      = Column(String(254), nullable=True)
    comentario = Column(Text, nullable=True)

    # Contexto clínico — último intercambio que disparó la alerta
    mensaje_alerta = Column(Text, nullable=False,
        comment="Mensaje del usuario que activó la señal de alerta")
    respuesta_ia   = Column(Text, nullable=False,
        comment="Respuesta de la IA en ese turno")

    # ── Derivación ──────────────────────────────────────────────────
    # estado: pendiente | derivado
    estado = Column(
        String(20), nullable=False, default="pendiente",
        comment="pendiente | derivado",
    )
    derivado_a_id = Column(
        UUID(as_uuid=True),
        ForeignKey("terapeutas.id", ondelete="SET NULL"),
        nullable=True,
        comment="Terapeuta interno al que se derivó el contacto",
    )
    nota_derivacion = Column(Text, nullable=True)
    derivado_en = Column(DateTime(timezone=True), nullable=True)

    creado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relación lazy para no cargar el terapeuta en cada consulta de lista
    terapeuta = relationship("Terapeuta", lazy="selectin")

    def __repr__(self):
        return f"<ContactoPublico nombre={self.nombre!r} estado={self.estado!r}>"
