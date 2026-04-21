# app/api/usuario_router.py
# CRUD de usuarios — protegido por rol
# Solo administradores pueden listar y modificar usuarios

from typing import List
from uuid import UUID
import uuid as _uuid

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.db.session import get_db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate
from app.api.deps import CurrentUser, require_roles

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# POST /api/v1/usuarios — solo admin: crear usuario
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin"))],
    summary="Crear nuevo usuario (admin)",
)
async def crear_usuario(
    data: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verificar email único
    existing = await db.execute(select(Usuario).where(Usuario.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado.")

    # Buscar el rol
    rol_q = await db.execute(select(Rol).where(Rol.key == data.rol))
    rol = rol_q.scalar_one_or_none()
    if not rol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Rol '{data.rol}' no existe.")

    n = (data.nombre or "")[:1].upper()
    a = (data.apellido or "")[:1].upper()
    nuevo = Usuario(
        id=_uuid.uuid4(),
        email=data.email,
        nombre=data.nombre,
        apellido=data.apellido,
        password_hash=_pwd.hash(data.password),
        rol_id=rol.id,
        avatar_initials=f"{n}{a}" or "?",
        avatar_class={"familia":"av-tl","ter-int":"av-tl","ter-ext":"av-pp","admin":"av-gr"}.get(data.rol, "av-gr"),
    )
    db.add(nuevo)
    await db.commit()

    result = await db.execute(select(Usuario).where(Usuario.id == nuevo.id))
    return result.scalar_one()


# ---------------------------------------------------------------------------
# GET /api/v1/usuarios — solo admin
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[UsuarioRead],
    dependencies=[Depends(require_roles("admin"))],
    summary="Listar todos los usuarios",
)
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    result = await db.execute(
        select(Usuario)
        .offset(skip)
        .limit(limit)
        .order_by(Usuario.creado_en.desc())
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /api/v1/usuarios/{id} — admin o el propio usuario
# ---------------------------------------------------------------------------
@router.get(
    "/{usuario_id}",
    response_model=UsuarioRead,
    summary="Obtener usuario por ID",
)
async def obtener_usuario(
    usuario_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Solo admin puede ver cualquier usuario; el resto solo se ve a sí mismo
    if current_user.rol != "admin" and current_user.id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permiso para ver este usuario"
        )

    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario


# ---------------------------------------------------------------------------
# PUT /api/v1/usuarios/{id} — admin o el propio usuario
# ---------------------------------------------------------------------------
@router.put(
    "/{usuario_id}",
    response_model=UsuarioRead,
    summary="Actualizar usuario",
)
async def actualizar_usuario(
    usuario_id: UUID,
    data: UsuarioUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    if current_user.rol != "admin" and current_user.id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permiso para modificar este usuario"
        )

    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Actualizar solo los campos enviados (partial update)
    update_data = data.model_dump(exclude_unset=True)

    # Si viene 'rol', buscar el objeto Rol y actualizar rol_id
    if "rol" in update_data:
        rol_key = update_data.pop("rol")
        rol_q = await db.execute(select(Rol).where(Rol.key == rol_key))
        rol_obj = rol_q.scalar_one_or_none()
        if not rol_obj:
            raise HTTPException(status_code=400, detail=f"Rol '{rol_key}' no existe.")
        usuario.rol_id = rol_obj.id

    for field, value in update_data.items():
        setattr(usuario, field, value)

    await db.commit()
    await db.refresh(usuario)
    return usuario


# ---------------------------------------------------------------------------
# DELETE /api/v1/usuarios/{id} — solo admin (soft delete)
# ---------------------------------------------------------------------------
@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
    summary="Desactivar usuario (soft delete)",
)
async def desactivar_usuario(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Soft delete — nunca borrar físicamente
    usuario.activo = False
    await db.commit()
