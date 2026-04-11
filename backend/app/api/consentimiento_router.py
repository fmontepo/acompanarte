# app/api/consentimiento_router.py

from app.api.base_router import create_router
from app.schemas.consentimiento import ConsentimientoCreate, ConsentimientoRead
from app.services.consentimiento_service import consentimiento_service

router = create_router(
    None,
    ConsentimientoCreate,
    ConsentimientoRead,
    consentimiento_service,
    "/consentimientos"
)