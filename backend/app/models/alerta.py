# app/models/alerta.py
# Módulo de Alertas — detección de señales sensibles en sesiones IA
# Principio arquitectónico: toda alerta debe ser revisada por un terapeuta humano
# antes de cerrar la interacción (Human-in-the-loop obligatorio)

from sqlalchemy import (
    Column, String, Boolean, Integer,
    Text, DateTime, ForeignKey, Index, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Alerta(Base):
    __tablename__ = "alertas"

    # ------------------------------------------------------------------
    # Identificación
    # ------------------------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Origen de la alerta
    sesion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sesiones_ia.id"),
        nullable=False,
        index=True,
    )
    mensaje_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mensajes_ia.id"),
        nullable=True,
        comment="Mensaje específico que disparó la alerta"
    )

    # Terapeuta que revisó la alerta
    revisada_por = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=True,
        comment="NULL mientras no fue revisada"
    )

    # ------------------------------------------------------------------
    # Clasificación de la alerta
    # tipo: crisis | riesgo | duda_diagnostica | escalamiento
    # severidad: 1 (baja) → 3 (crítica)
    # ------------------------------------------------------------------
    tipo = Column(
        String(30),
        nullable=False,
        index=True,
        comment="crisis | riesgo | duda_diagnostica | escalamiento"
    )
    severidad = Column(
        Integer,
        nullable=False,
        default=1,
        comment="1=baja | 2=media | 3=crítica"
    )
    descripcion = Column(
        Text,
        nullable=False,
        comment="Descripción generada automáticamente por el filtro IA"
    )

    # ------------------------------------------------------------------
    # Estado de resolución
    # resuelta=False por default — requiere acción humana explícita
    # ------------------------------------------------------------------
    resuelta = Column(Boolean, nullable=False, default=False, index=True)
    nota_resolucion = Column(
        Text,
        nullable=True,
        comment="Nota del terapeuta al resolver la alerta"
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    creada_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    resuelta_en = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Índices compuestos para queries frecuentes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_alerta_pendiente", "resuelta", "severidad", "creada_en"),
        Index("idx_alerta_sesion_resuelta", "sesion_id", "resuelta"),
    )

    # ------------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------------
    sesion = relationship("SesionIA", lazy="selectin")
    mensaje = relationship("MensajeIA", lazy="selectin")
    revisor = relationship("Usuario", foreign_keys=[revisada_por], lazy="selectin")

    def __repr__(self):
        return f"<Alerta tipo={self.tipo} severidad={self.severidad} resuelta={self.resuelta}>"
