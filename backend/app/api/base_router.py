# app/api/base_router.py
# Router base genérico async — genera CRUD estándar para cualquier entidad
# Los routers específicos que necesiten lógica extra NO usan este base_router,
# lo implementan directamente (ej: auth_router, alerta_router, recurso_router)

from typing import Type, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.services.base_service import BaseService
from app.api.deps import get_current_user


def create_router(
    model,
    schema_create: Type[BaseModel],
    schema_read: Type[BaseModel],
    service: BaseService,
    prefix: str,
    tags: list = None,
    require_auth: bool = True,
) -> APIRouter:
    """
    Genera un router FastAPI async con CRUD completo.
    Parámetros:
        model: modelo SQLAlchemy (puede ser None si el service ya lo tiene)
        schema_create: schema Pydantic para creación
        schema_read: schema Pydantic para respuesta
        service: instancia de BaseService o subclase
        prefix: prefijo de la ruta, ej: '/pacientes'
        tags: lista de tags para Swagger
        require_auth: si True, todos los endpoints requieren JWT
    """
    router = APIRouter(
        prefix=prefix,
        tags=tags or [prefix.strip("/")],
    )

    auth_dep = [Depends(get_current_user)] if require_auth else []

    @router.post(
        "/",
        response_model=schema_read,
        status_code=status.HTTP_201_CREATED,
        dependencies=auth_dep,
    )
    async def create(
        data: schema_create,
        db: AsyncSession = Depends(get_db),
    ):
        return await service.create(db, data)

    @router.get(
        "/",
        response_model=List[schema_read],
        dependencies=auth_dep,
    )
    async def get_all(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
    ):
        return await service.get_all(db, skip=skip, limit=limit)

    @router.get(
        "/{id}",
        response_model=schema_read,
        dependencies=auth_dep,
    )
    async def get_one(
        id: UUID,
        db: AsyncSession = Depends(get_db),
    ):
        obj = await service.get(db, id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registro no encontrado"
            )
        return obj

    @router.put(
        "/{id}",
        response_model=schema_read,
        dependencies=auth_dep,
    )
    async def update(
        id: UUID,
        data: schema_create,
        db: AsyncSession = Depends(get_db),
    ):
        obj = await service.update(db, id, data)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro no encontrado"
            )
        return obj

    @router.delete(
        "/{id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=auth_dep,
    )
    async def delete(
        id: UUID,
        db: AsyncSession = Depends(get_db),
    ):
        obj = await service.delete(db, id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro no encontrado"
            )

    return router
