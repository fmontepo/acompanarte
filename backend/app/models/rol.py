"""
acompañarte — Modelo: roles
Tabla de configuración de roles de acceso.
Desacopla la lógica de permisos del modelo de usuario.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class Rol(Base):
    __tablename__ = "roles"

    # ── Identidad ──────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Clave técnica usada en código y JWT.
    # Valores: familia | ter-int | ter-ext | admin
    key = Column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
        comment="Clave técnica del rol: familia | ter-int | ter-ext | admin",
    )

    # ── Presentación (UI) ──────────────────────────────────────────
    label = Column(
        String(100),
        nullable=False,
        comment="Texto visible en el sidebar y topbar de la app",
    )

    # Ruta React a la que se redirige después del login.
    # Ej: /familiar/dashboard
    default_path = Column(
        String(200),
        nullable=False,
        comment="Ruta frontend por defecto al iniciar sesión",
    )

    # Estructura del sidebar en JSON.
    # Formato: [{ section: str, items: [{ id, icon, label, badge? }] }]
    # El frontend lo lee directamente para construir la navegación,
    # sin necesidad de hardcodear nada en el cliente.
    nav_config = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Configuración de secciones y items del sidebar",
    )

    # ── Metadatos ──────────────────────────────────────────────────
    activo = Column(Boolean, nullable=False, default=True)

    creado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # ── Relaciones ─────────────────────────────────────────────────
    usuarios = relationship(
        "Usuario",
        back_populates="rol",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Rol key={self.key!r} label={self.label!r}>"
