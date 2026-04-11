# app/api/auth_router.py
# Endpoints de autenticación: login · register · me
# Contrato API definido en arquitectura: POST /auth/login · POST /auth/register · GET /auth/me

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from passlib.context import CryptContext
import os
import uuid

from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.api.deps import CurrentUser

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, rol: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "rol": rol,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------
@router.post("/login", summary="Iniciar sesión")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Usuario).where(Usuario.email == form_data.username)
    )
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        # Incrementar intentos fallidos
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

    # Reset intentos fallidos y registrar último login
    usuario.intentos_fallidos = 0
    usuario.ultimo_login = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(str(usuario.id), usuario.rol)
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": usuario.rol,
        "nombre": usuario.nombre,
    }


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register
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
    # Verificar email único
    result = await db.execute(
        select(Usuario).where(Usuario.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado"
        )

    nuevo = Usuario(
        id=uuid.uuid4(),
        email=data.email,
        password_hash=hash_password(data.password),
        nombre=data.nombre,
        apellido=data.apellido,
        telefono=data.telefono,
        fecha_nacimiento=data.fecha_nacimiento,
        rol=data.rol,
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)
    return nuevo


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UsuarioRead,
    summary="Perfil del usuario autenticado",
)
async def me(current_user: CurrentUser):
    return current_user
