# app/models/recursoProfesional.py
# Recursos bibliográficos validados por terapeutas — alimentan el sistema RAG
# FLUJO: subido por terapeuta → pendiente validación → validado por terapeuta senior
# Solo recursos con validado=True son usados por el módulo RAG

from sqlalchemy import (
    Column, String, Boolean, Text,
    DateTime, ForeignKey, Index, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid

from app.db.base import Base

# Dimensión del embedding — debe coincidir con el modelo de sentence-transformers
# paraphrase-multilingual-MiniLM-L12-v2 → 384 dimensiones
# text-embedding-3-small (OpenAI) → 1536 dimensiones
# Usar 384 para modelo local, 1536 si se migra a API externa
EMBEDDING_DIM = 384


class RecursoProfesional(Base):
    __tablename__ = "recursos_profesionales"

    # ------------------------------------------------------------------
    # Identificación
    # ------------------------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Quién subió el recurso
    subido_por = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )

    # Quién lo validó (NULL = pendiente de validación)
    validado_por = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=True,
        comment="NULL mientras no fue validado por un terapeuta"
    )

    # ------------------------------------------------------------------
    # Contenido del recurso
    # ------------------------------------------------------------------
    titulo = Column(String, nullable=False)
    descripcion = Column(Text)

    # tipo: pdf | articulo | guia | protocolo
    tipo = Column(
        String(20),
        nullable=False,
        comment="pdf | articulo | guia | protocolo"
    )

    # Ruta al archivo en el object storage local
    url_storage = Column(
        String,
        nullable=True,
        comment="Ruta relativa al archivo en el servidor"
    )

    # Texto extraído del documento (para búsqueda full-text)
    contenido_texto = Column(
        Text,
        nullable=True,
        comment="Texto extraído del PDF para indexación"
    )

    # ------------------------------------------------------------------
    # Estado de validación
    # validado=False por default — requiere aprobación explícita
    # Solo recursos validados son usados en el RAG
    # ------------------------------------------------------------------
    validado = Column(Boolean, nullable=False, default=False, index=True)
    activo = Column(Boolean, nullable=False, default=True)

    # ------------------------------------------------------------------
    # Embedding vectorial para búsqueda semántica (RAG)
    # Se genera automáticamente al subir/validar el recurso
    # ------------------------------------------------------------------
    embedding = Column(
        Vector(EMBEDDING_DIM),
        nullable=True,
        comment=f"Vector de {EMBEDDING_DIM} dimensiones para búsqueda semántica RAG"
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    subido_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    validado_en = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    actualizado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ------------------------------------------------------------------
    # Índices
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_recurso_validado_activo", "validado", "activo"),
        Index("idx_recurso_tipo", "tipo"),
    )

    # ------------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------------
    autor = relationship("Usuario", foreign_keys=[subido_por], lazy="selectin")
    validador = relationship("Usuario", foreign_keys=[validado_por], lazy="selectin")

    def __repr__(self):
        return f"<RecursoProfesional titulo={self.titulo!r} validado={self.validado}>"
