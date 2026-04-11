# app/api/vinculo_router.py

from app.api.base_router import create_router
from app.schemas.vinculo import VinculoCreate, VinculoRead
from app.services.vinculo_service import vinculo_service

router = create_router(
    None,
    VinculoCreate,
    VinculoRead,
    vinculo_service,
    "/vinculos"
)