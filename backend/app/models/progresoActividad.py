# app/models/progresoActividad.py
# Registro de progreso de una actividad terapéutica realizada en casa
# El familiar completa este registro — el terapeuta lo revisa

from sqlalchemy import Column, DateTime, Text, ForeignKey, Integer, Boolean, String, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from app.db.base import Base

EMBEDDING_DIM = 384


class ProgresoActividad(Base):
    __tablename__ = "progreso_actividad"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    actividad_id = Column(
        UUID(as_uuid=True),
        ForeignKey("actividades_familiar.id"),
        nullable=False,
        index=True,
    )
    familiar_id = Column(
        UUID(as_uuid=True),
        ForeignKey("familiares.id"),
        nullable=False,
        index=True,
    )

    observacion = Column(Text, nullable=True, comment="Observación del familiar sobre la actividad")

    # multimedia: lista de rutas a archivos subidos (fotos, videos)
    # Estructura: [{"tipo": "imagen", "url": "...", "nombre": "..."}]
    multimedia = Column(JSONB, nullable=True, comment="Archivos adjuntos al progreso")

    # ── Seguimiento de etapas ────────────────────────────────────────────────
    # True  = la actividad se completó en su totalidad
    # False = se avanzó parcialmente (solo algunas etapas)
    es_completada = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="True si se completaron todas las etapas; False si fue parcial",
    )
    # Cuántas etapas se hicieron en esta sesión.
    # NULL cuando es_completada=True (se asume total_etapas de la actividad).
    etapas_completadas = Column(
        Integer,
        nullable=True,
        comment="Etapas realizadas en esta sesión. NULL = todas (es_completada=True).",
    )

    # Escala de satisfacción: 1 (muy difícil) → 5 (excelente)
    nivel_satisfaccion = Column(
        Integer,
        nullable=True,
        comment="Escala 1-5: 1=muy difícil, 5=excelente",
    )

    completada_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # ── Embedding RAG clínico ────────────────────────────────────────────────
    # Solo se genera si el registro tiene observacion (campo de texto libre)
    embedding = Column(
        Vector(EMBEDDING_DIM),
        nullable=True,
        comment=f"Vector {EMBEDDING_DIM}d para RAG clínico interno",
    )
    embedding_hash = Column(
        String(64),
        nullable=True,
        comment="SHA-256 del texto fuente; permite skip si no hubo cambios",
    )

    __table_args__ = (
        Index("idx_progreso_actividad_familiar", "actividad_id", "familiar_id"),
    )

    actividad = relationship("ActividadFamiliar", back_populates="progresos", lazy="selectin")
    familiar = relationship("Familiar", lazy="selectin")

    def __repr__(self):
        return f"<ProgresoActividad satisfaccion={self.nivel_satisfaccion}>"
