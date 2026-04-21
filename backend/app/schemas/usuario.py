# app/schemas/usuario.py
# Schemas Pydantic para Usuario — validación de entrada y salida de la API
# Patrón: Base → Create → Update → Read

from pydantic import BaseModel, EmailStr, field_validator, model_validator
from uuid import UUID
from datetime import date, datetime
from typing import Optional
import re


# ---------------------------------------------------------------------------
# Roles válidos del sistema (coinciden con roles.key en la DB)
# ---------------------------------------------------------------------------
ROLES_VALIDOS = {"admin", "familia", "ter-int", "ter-ext"}


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
            raise ValueError(f"Rol inválido. Valores aceptados: {sorted(ROLES_VALIDOS)}")
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
    activo: Optional[bool] = None      # admin: activar / desactivar usuario
    rol: Optional[str] = None          # admin: cambiar rol

    @field_validator("nombre", "apellido", mode="before")
    @classmethod
    def no_vacio_si_presente(cls, v):
        if v is not None and not str(v).strip():
            raise ValueError("El campo no puede estar vacío")
        return v

    @field_validator("rol")
    @classmethod
    def validar_rol_si_presente(cls, v):
        if v is not None and v not in {"admin", "familia", "ter-int", "ter-ext"}:
            raise ValueError(f"Rol inválido: {v}")
        return v


# ---------------------------------------------------------------------------
# Read — respuesta de la API (nunca expone password_hash)
# Maneja tanto dict como instancias del modelo SQLAlchemy (rol es relación).
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
    email_verificado: bool = False
    bloqueado: bool
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    ultimo_login: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def extraer_rol_relacion(cls, v):
        """
        Cuando `v` es una instancia SQLAlchemy, `v.rol` es el objeto Rol
        (relación ORM), no un string. Este validador extrae `rol.key`.
        """
        if hasattr(v, "__tablename__"):
            rol_obj = getattr(v, "rol", None)
            rol_key = (rol_obj.key if rol_obj and hasattr(rol_obj, "key") else "")
            return {
                "id":               v.id,
                "email":            v.email,
                "nombre":           v.nombre or "",
                "apellido":         v.apellido or "",
                "telefono":         getattr(v, "telefono", None),
                "fecha_nacimiento": getattr(v, "fecha_nacimiento", None),
                "domicilio":        getattr(v, "domicilio", None),
                "rol":              rol_key,
                "activo":           v.activo,
                "email_verificado": getattr(v, "email_verificado", False),
                "bloqueado":        v.bloqueado,
                "creado_en":        v.creado_en,
                "actualizado_en":   v.actualizado_en,
                "ultimo_login":     v.ultimo_login,
            }
        return v


# ---------------------------------------------------------------------------
# Token — respuesta del login
# ---------------------------------------------------------------------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre: str
