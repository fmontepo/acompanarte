# app/services/base_service.py
# Service base genérico async — todos los services heredan de este
# La lógica de negocio específica va en cada service hijo

from typing import Generic, TypeVar, Type, Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.repositories.base import CRUDBase

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType]):

    def __init__(self, model: Type[ModelType]):
        self.repo = CRUDBase(model)
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        return await self.repo.get(db, id)

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        return await self.repo.get_all(db, skip=skip, limit=limit)

    async def create(self, db: AsyncSession, data: BaseModel) -> ModelType:
        obj = self.model(**data.model_dump(exclude_unset=True))
        return await self.repo.create(db, obj)

    async def update(
        self,
        db: AsyncSession,
        id: UUID,
        data: BaseModel,
    ) -> Optional[ModelType]:
        db_obj = await self.repo.get(db, id)
        if not db_obj:
            return None
        return await self.repo.update(
            db, db_obj, data.model_dump(exclude_unset=True)
        )

    async def delete(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        return await self.repo.soft_delete(db, id)
