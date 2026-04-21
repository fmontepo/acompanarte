"""
acompañarte — Modelo: usuarios (reestructurado)
Cambios respecto a la versión anterior:
  - Se elimina la columna `rol` (VARCHAR/ENUM hardcodeado)
  - Se agrega `rol_id` (UUID FK → roles.id)
  - Se agrega `avatar_initials` y `avatar_class` para la UI
  - Se agrega `profile_label` (texto descriptivo del perfil)
  - Todos los demás campos existentes se preservan sin modificación
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    # ── Identidad ──────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    nombre = Column(String(100), nullable=True)
    apellido = Column(String(100), nullable=True)

    # ── Rol (FK a tabla roles) ─────────────────────────────────────
    # Reemplaza la columna `rol` VARCHAR/ENUM anterior.
    # La FK permite JOIN directo para obtener nav_config y default_path
    # sin ningún mapeo en el frontend.
    rol_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK a roles.id — reemplaza la columna rol VARCHAR",
    )

    # ── Presentación UI ────────────────────────────────────────────
    # Iniciales para el avatar (ej: "ML", "AG").
    # Se genera automáticamente en el servicio si no se provee.
    avatar_initials = Column(
        String(4),
        nullable=True,
        comment="Iniciales para el avatar: ML | AG | LR...",
    )

    # Clase CSS del avatar (ej: "av-tl", "av-pp", "av-gr").
    # Determina el color del círculo de avatar en el frontend.
    avatar_class = Column(
        String(20),
        nullable=True,
        comment="Clase CSS del avatar: av-tl | av-pp | av-gr...",
    )

    # Texto descriptivo que aparece bajo el nombre en el perfil.
    # Ej: "Familiar · Tutora legal de Tomás Pérez"
    profile_label = Column(
        String(200),
        nullable=True,
        comment="Descripción del perfil visible en la app",
    )

    # ── Estado de la cuenta ────────────────────────────────────────
    # Campos preservados de la versión anterior sin modificación
    activo = Column(Boolean, nullable=False, default=True)
    email_verificado = Column(Boolean, nullable=False, default=False)
    bloqueado = Column(Boolean, nullable=False, default=False)
    intentos_fallidos = Column(Integer, nullable=False, default=0)
    bloqueado_hasta = Column(DateTime(timezone=True), nullable=True)

    # ── Auditoría ──────────────────────────────────────────────────
    creado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    actualizado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    ultimo_login = Column(DateTime(timezone=True), nullable=True)

    # ── Relaciones ─────────────────────────────────────────────────
    rol = relationship(
        "Rol",
        back_populates="usuarios",
        lazy="joined",   # siempre hace JOIN: nav_config llega en una sola query
    )

    # Relaciones existentes — se preservan sin modificación
    familiar = relationship(
        "Familiar",
        back_populates="usuario",
        uselist=False,
        lazy="select",
    )
    terapeuta = relationship(
        "Terapeuta",
        back_populates="usuario",
        uselist=False,
        lazy="select",
    )
    administrador = relationship(
        "Administrador",
        back_populates="usuario",
        uselist=False,
        lazy="select",
    )
    consentimientos = relationship(
        "Consentimiento",
        back_populates="usuario",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Usuario email={self.email!r} rol_id={self.rol_id}>"
