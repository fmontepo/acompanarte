# app/models/auditoria.py
# Log de auditoría inmutable — trazabilidad legal (Ley 25.326 / GDPR)
# REGLAS:
#   - Nunca modificar ni borrar registros de auditoría
#   - El timestamp es obligatorio y lo pone el servidor (no la app)
#   - Registrar TODA acción sobre datos sensibles: acceso, modificación, borrado

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class EventoAuditoria(Base):
    __tablename__ = "auditoria"

    # ------------------------------------------------------------------
    # Identificación
    # ------------------------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Usuario que realizó la acción (nullable: puede ser anónimo/sistema)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
        comment="NULL si la acción fue del sistema o de un usuario no autenticado"
    )

    # ------------------------------------------------------------------
    # Descripción de la acción
    # accion: login | logout | ver | crear | modificar | eliminar | exportar | denegar
    # ------------------------------------------------------------------
    accion = Column(
        String(30),
        nullable=False,
        index=True,
        comment="login | logout | ver | crear | modificar | eliminar | exportar | denegar"
    )

    # Entidad afectada: usuarios | pacientes | sesiones_ia | recursos | ...
    recurso_tipo = Column(
        String(50),
        nullable=False,
        comment="Nombre de la tabla/entidad afectada"
    )

    # ID del registro específico afectado
    recurso_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID del registro afectado — NULL si aplica a múltiples"
    )

    # ------------------------------------------------------------------
    # Contexto técnico
    # ------------------------------------------------------------------
    ip_origen = Column(
        String(45),
        nullable=True,
        comment="IPv4 o IPv6 del cliente — máx 45 chars para IPv6"
    )

    # Resultado: ok | denegado | error
    resultado = Column(
        String(10),
        nullable=False,
        default="ok",
        comment="ok | denegado | error"
    )

    # Metadatos adicionales: user-agent, parámetros, razón de denegación, etc.
    metadata_extra = Column(
        JSONB,
        nullable=True,
        comment="Datos adicionales del evento en formato JSON"
    )

    # ------------------------------------------------------------------
    # Timestamp — CRÍTICO: nullable=False + server_default
    # El servidor pone el timestamp — nunca la aplicación
    # Garantiza trazabilidad legal aunque haya bug en la app
    # ------------------------------------------------------------------
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp inmutable puesto por el servidor PostgreSQL"
    )

    # ------------------------------------------------------------------
    # Índices para queries de auditoría frecuentes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_auditoria_usuario_ts", "usuario_id", "timestamp"),
        Index("idx_auditoria_recurso", "recurso_tipo", "recurso_id"),
        Index("idx_auditoria_accion_resultado", "accion", "resultado"),
    )

    # ------------------------------------------------------------------
    # Relaciones (solo lectura — nunca modificar desde aquí)
    # ------------------------------------------------------------------
    usuario = relationship("Usuario", lazy="selectin")

    def __repr__(self):
        return (
            f"<EventoAuditoria accion={self.accion} "
            f"recurso={self.recurso_tipo} resultado={self.resultado}>"
        )
