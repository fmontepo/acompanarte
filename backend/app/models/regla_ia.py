# app/models/regla_ia.py
# Reglas de comportamiento para el Asistente IA (público y autenticado)
#
# positiva → lo que el asistente PUEDE y DEBE responder
# negativa → lo que el asistente NO debe responder ni hacer
#
# Las reglas activas se inyectan en cada prompt generado por ia_service.
# El admin puede crearlas, editarlas, reordenarlas y desactivarlas sin
# necesidad de desplegar código nuevo.

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class ReglaIA(Base):
    __tablename__ = "reglas_ia"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 'positiva' | 'negativa'
    tipo = Column(
        String(10),
        nullable=False,
        index=True,
        comment="positiva (qué puede hacer) | negativa (qué no puede hacer)",
    )

    # 'familiar' | 'terapeuta' | 'global'
    # global → se aplica a ambos módulos
    contexto = Column(
        String(15),
        nullable=False,
        default="global",
        server_default="global",
        index=True,
        comment="familiar | terapeuta | global (aplica a ambos)",
    )

    # Texto de la regla — se inyecta literalmente en el prompt
    texto = Column(
        Text,
        nullable=False,
        comment="Texto de la regla que se incluye en el prompt del modelo",
    )

    # Descripción interna para el admin — no se envía al modelo
    descripcion = Column(
        String(300),
        nullable=True,
        comment="Descripción interna para el admin (no va al prompt)",
    )

    # Solo las reglas activas se inyectan en el prompt
    activa = Column(Boolean, nullable=False, default=True, index=True)

    # Orden de aparición dentro de su tipo (menor = primero)
    orden = Column(Integer, nullable=False, default=0)

    creado_en = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actualizado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<ReglaIA tipo={self.tipo!r} activa={self.activa} orden={self.orden}>"
