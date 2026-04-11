# app/repositories/base.py
# Repositorio base genérico — patrón Repository con async SQLAlchemy 2.x
# Todos los repositorios específicos heredan de esta clase

from typing import Generic, TypeVar, Type, Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType")


class CRUDBase(Generic[ModelType]):

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        result = await db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj: ModelType) -> ModelType:
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        data: dict,
    ) -> ModelType:
        for key, value in data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def soft_delete(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        """Soft delete — marca activo=False, nunca borra físicamente."""
        obj = await self.get(db, id)
        if obj and hasattr(obj, "activo"):
            obj.activo = False
            await db.commit()
        return obj
