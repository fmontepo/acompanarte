# app/schemas/usuario.py
# Schemas Pydantic para Usuario — validación de entrada y salida de la API
# Patrón: Base → Create → Update → Read

from pydantic import BaseModel, EmailStr, field_validator, model_validator
from uuid import UUID
from datetime import date, datetime
from typing import Optional
import re


# ---------------------------------------------------------------------------
# Roles válidos del sistema
# ---------------------------------------------------------------------------
ROLES_VALIDOS = {"admin", "terapeuta", "familiar"}


# ---------------------------------------------------------------------------
# Base — campos comunes a todos los schemas
# ---------------------------------------------------------------------------
class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    apellido: str
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    domicilio: Optional[str] = None
    rol: str

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v: str) -> str:
        if v not in ROLES_VALIDOS:
            raise ValueError(f"Rol inválido. Valores aceptados: {ROLES_VALIDOS}")
        return v

    @field_validator("nombre", "apellido")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v.strip()


# ---------------------------------------------------------------------------
# Create — para registro de nuevo usuario
# ---------------------------------------------------------------------------
class UsuarioCreate(UsuarioBase):
    password: str

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v


# ---------------------------------------------------------------------------
# Update — actualización parcial (todos los campos opcionales)
# ---------------------------------------------------------------------------
class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    domicilio: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator("nombre", "apellido", mode="before")
    @classmethod
    def no_vacio_si_presente(cls, v):
        if v is not None and not str(v).strip():
            raise ValueError("El campo no puede estar vacío")
        return v


# ---------------------------------------------------------------------------
# Read — respuesta de la API (nunca expone password_hash)
# ---------------------------------------------------------------------------
class UsuarioRead(BaseModel):
    id: UUID
    email: EmailStr
    nombre: str
    apellido: str
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    domicilio: Optional[str] = None
    rol: str
    activo: bool
    email_verificado: bool
    bloqueado: bool
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    ultimo_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Token — respuesta del login
# ---------------------------------------------------------------------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre: str
