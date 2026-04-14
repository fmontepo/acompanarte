# app/models/ia.py
# Modelos del módulo de IA — SesionIA y MensajeIA
# RESTRICCIONES (no negociables según arquitectura):
#   - La IA nunca accede a datos identificativos
#   - El contenido almacenado es siempre anonimizado
#   - Toda interacción queda registrada para auditoría
#   - fuentes_rag registra qué recursos validados se usaron

from sqlalchemy import (
    Column, String, Boolean, Text,
    DateTime, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class SesionIA(Base):
    __tablename__ = "sesiones_ia"

    # ------------------------------------------------------------------
    # Identificación
    # ------------------------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK al familiar que inicia la sesión
    familiar_id = Column(
        UUID(as_uuid=True),
        ForeignKey("familiares.id"),
        nullable=False,
        index=True,
    )

    # FK opcional al paciente de referencia
    paciente_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pacientes.id"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Estado de la sesión
    # Estado: activa | cerrada | escalada
    # ------------------------------------------------------------------
    estado = Column(
        String(20),
        nullable=False,
        default="activa",
        comment="activa | cerrada | escalada"
    )

    # Contexto anonimizado que se pasa al modelo — sin PII
    # Estructura: {"edad_aproximada": "...", "contexto_clinico": "..."}
    contexto_anonimo = Column(
        JSONB,
        nullable=True,
        comment="Contexto pre-procesado sin datos identificativos"
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    iniciada_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    cerrada_en = Column(DateTime(timezone=True))

    # ------------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------------
    familiar = relationship("Familiar", lazy="selectin")
    paciente = relationship("Paciente", back_populates="sesiones_ia", lazy="selectin")
    mensajes = relationship(
        "MensajeIA",
        back_populates="sesion",
        lazy="dynamic",
        order_by="MensajeIA.enviado_en",
    )

    def __repr__(self):
        return f"<SesionIA id={self.id} estado={self.estado}>"


class MensajeIA(Base):
    __tablename__ = "mensajes_ia"

    # ------------------------------------------------------------------
    # Identificación
    # ------------------------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    sesion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sesiones_ia.id"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Contenido
    # IMPORTANTE: el contenido almacenado es SIEMPRE anonimizado.
    # El preprocesador del módulo IA elimina PII antes de persistir.
    # ------------------------------------------------------------------
    contenido = Column(
        Text,
        nullable=False,
        comment="Contenido anonimizado — sin PII"
    )

    # emisor: 'usuario' | 'ia'
    emisor = Column(
        String(10),
        nullable=False,
        comment="usuario | ia"
    )

    # ------------------------------------------------------------------
    # Seguridad y trazabilidad
    # ------------------------------------------------------------------
    genera_alerta = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True si el mensaje disparó una alerta de escalamiento"
    )

    # Recursos RAG utilizados para generar la respuesta
    # Estructura: [{"recurso_id": "uuid", "titulo": "...", "score": 0.87}]
    fuentes_rag = Column(
        JSONB,
        nullable=True,
        comment="Recursos profesionales usados como contexto RAG"
    )

    # Flag de seguridad: la respuesta pasó el filtro anti-diagnóstico
    filtro_aplicado = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True si el filtro anti-diagnóstico fue aplicado"
    )

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------
    enviado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # ------------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------------
    sesion = relationship("SesionIA", back_populates="mensajes")

    def __repr__(self):
        return f"<MensajeIA emisor={self.emisor} alerta={self.genera_alerta}>"
