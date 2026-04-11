from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.parentesco import Parentesco
from app.schemas.parentesco import ParentescoRead
from app.api.deps import get_current_user

router = APIRouter(prefix="/parentescos", tags=["Parentescos"])

@router.get("/", response_model=List[ParentescoRead])
async def listar_parentescos(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Parentesco).order_by(Parentesco.nombre))
    return result.scalars().all()
