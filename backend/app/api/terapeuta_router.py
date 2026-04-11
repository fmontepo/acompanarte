# app/api/terapeuta_router.py

from app.api.base_router import create_router
from app.schemas.terapeuta import TerapeutaCreate, TerapeutaRead
from app.services.terapeuta_service import terapeuta_service

router = create_router(
    None,
    TerapeutaCreate,
    TerapeutaRead,
    terapeuta_service,
    "/terapeutas"
)