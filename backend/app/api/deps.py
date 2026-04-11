# app/api/deps.py
# Dependencias reutilizables para inyección en todos los routers.
# Implementa: validación JWT · extracción de usuario · control RBAC

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.db.session import get_db
from app.models.usuario import Usuario

# ---------------------------------------------------------------------------
# Configuración JWT — leer desde variables de entorno
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    raise Exception("SECRET_KEY no está definida en las variables de entorno")

# El endpoint que emite el token (usado por OAuth2PasswordBearer)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ---------------------------------------------------------------------------
# Tipos reutilizables para anotaciones
# ---------------------------------------------------------------------------
DBDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


# ---------------------------------------------------------------------------
# Función base: extraer y validar el JWT
# ---------------------------------------------------------------------------
async def get_current_user(
    token: TokenDep,
    db: DBDep,
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(Usuario).where(Usuario.id == user_id)
    )
    usuario = result.scalar_one_or_none()

    if usuario is None:
        raise credentials_exception

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    if usuario.bloqueado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario bloqueado. Contacte al administrador."
        )

    return usuario


# ---------------------------------------------------------------------------
# Dependencia anotada: usuario autenticado
# Uso: current_user: CurrentUser = Depends()
# ---------------------------------------------------------------------------
CurrentUser = Annotated[Usuario, Depends(get_current_user)]


# ---------------------------------------------------------------------------
# RBAC — control de roles
# Uso: current_user: CurrentUser = Depends(require_roles("admin", "terapeuta"))
# ---------------------------------------------------------------------------
def require_roles(*roles: str):
    """
    Factory que devuelve una dependencia FastAPI que valida el rol del usuario.
    Ejemplo: Depends(require_roles("admin", "terapeuta"))
    """
    async def role_checker(
        current_user: CurrentUser,
    ) -> Usuario:
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles permitidos: {', '.join(roles)}"
            )
        return current_user
    return role_checker


# ---------------------------------------------------------------------------
# Dependencias de rol predefinidas — listas para usar en cualquier router
# ---------------------------------------------------------------------------
def require_admin():
    return Depends(require_roles("admin"))

def require_terapeuta():
    return Depends(require_roles("admin", "terapeuta"))

def require_familiar():
    return Depends(require_roles("admin", "terapeuta", "familiar"))
