"""
acompañarte — Schemas: auth
Contrato de datos entre el endpoint /auth/login y el AuthContext del frontend.
"""
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr


# ── Request ──────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Usuario embebido en la respuesta de login ─────────────────────
# El frontend guarda este objeto completo en localStorage y en el
# AuthContext. Incluye todo lo necesario para construir la UI sin
# ninguna lógica de roles en el cliente.
class UsuarioLoginOut(BaseModel):
    id:               uuid.UUID
    email:            EmailStr
    nombre:           str | None
    apellido:         str | None

    # Campos que vienen de la tabla roles (vía JOIN)
    rol_key:          str          # 'familia' | 'ter-int' | 'ter-ext' | 'admin'
    label:            str          # 'Panel familiar' | 'Terapeuta interno'...
    default_path:     str          # '/familiar/dashboard' | '/admin/dashboard'...
    nav_config:       list[Any]    # Estructura del sidebar — lista de secciones

    # Campos de presentación visual
    avatar_initials:  str | None   # 'ML' | 'AG' | 'LR'
    avatar_class:     str | None   # 'av-tl' | 'av-pp' | 'av-gr'
    profile_label:    str | None   # 'Familiar · Tutora legal de Tomás Pérez'

    class Config:
        from_attributes = True


# ── Respuesta completa del login ──────────────────────────────────
class LoginResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UsuarioLoginOut


# ── Schemas de rol (para endpoints admin) ─────────────────────────
class RolOut(BaseModel):
    id:           uuid.UUID
    key:          str
    label:        str
    default_path: str
    nav_config:   list[Any]
    activo:       bool
    creado_en:    datetime

    class Config:
        from_attributes = True


class RolUpdate(BaseModel):
    label:        str | None = None
    default_path: str | None = None
    nav_config:   list[Any]  | None = None
    activo:       bool        | None = None
