# app/api/auth_router.py
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload  # noqa: already imported
from jose import jwt
from passlib.context import CryptContext
import os
import uuid

from app.db.session import get_db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.api.deps import CurrentUser

router = APIRouter(prefix="/auth", tags=["Autenticación"])

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, rol_key: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub":     subject,
        "rol_key": rol_key,
        "exp":     expire,
        "iat":     datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------
@router.post("/login", summary="Iniciar sesión")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(Usuario.email == form_data.username)
    )
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        if usuario:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= 5:
                usuario.bloqueado = True
                usuario.bloqueado_hasta = datetime.now(timezone.utc) + timedelta(minutes=30)
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if usuario.bloqueado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario bloqueado. Contacte al administrador."
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    usuario.intentos_fallidos = 0
    usuario.ultimo_login = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(str(usuario.id), usuario.rol.key)

    return {
        "access_token": token,
        "token_type":   "bearer",
        "user": {
            "id":              str(usuario.id),
            "email":           usuario.email,
            "nombre":          usuario.nombre,
            "apellido":        usuario.apellido,
            "rol_key":         usuario.rol.key,
            "label":           usuario.rol.label,
            "default_path":    usuario.rol.default_path,
            "nav_config":      usuario.rol.nav_config,
            "avatar_initials": usuario.avatar_initials,
            "avatar_class":    usuario.avatar_class,
            "profile_label":   usuario.profile_label,
        },
    }


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
)
async def register(
    data: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Usuario).where(Usuario.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado"
        )

    rol_result = await db.execute(
        select(Rol).where(Rol.key == data.rol)
    )
    rol = rol_result.scalar_one_or_none()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol '{data.rol}' no existe en el sistema"
        )

    nuevo = Usuario(
        id=uuid.uuid4(),
        email=data.email,
        password_hash=hash_password(data.password),
        nombre=data.nombre,
        apellido=data.apellido,
        rol_id=rol.id,
        avatar_initials=_initials(data.nombre, data.apellido),
        avatar_class=_avatar_class(rol.key),
    )
    db.add(nuevo)
    await db.commit()

    # Recargar con la relación rol cargada (necesario para serializar UsuarioRead)
    result = await db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(Usuario.id == nuevo.id)
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UsuarioRead,
    summary="Perfil del usuario autenticado",
)
async def me(current_user: CurrentUser):
    return current_user


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------
def _initials(nombre: str | None, apellido: str | None) -> str:
    n = (nombre or "")[:1].upper()
    a = (apellido or "")[:1].upper()
    return f"{n}{a}" or "?"


def _avatar_class(rol_key: str) -> str:
    return {
        "familia":  "av-tl",
        "ter-int":  "av-tl",
        "ter-ext":  "av-pp",
        "admin":    "av-gr",
    }.get(rol_key, "av-gr")
