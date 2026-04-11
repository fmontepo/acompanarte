# app/api/usuario_router.py
# CRUD de usuarios — protegido por rol
# Solo administradores pueden listar y modificar usuarios

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate
from app.api.deps import CurrentUser, require_roles

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


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
        .where(Usuario.activo == True)
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
