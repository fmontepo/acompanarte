# app/api/parentesco_router.py

from app.api.base_router import create_router
from app.schemas.parentesco import ParentescoCreate, ParentescoRead
from app.services.parentesco_service import parentesco_service

router = create_router(
    None,
    ParentescoCreate,
    ParentescoRead,
    parentesco_service,
    "/parentescos"
)