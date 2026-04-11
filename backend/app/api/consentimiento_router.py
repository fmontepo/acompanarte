from app.api.base_router import create_router
from app.schemas.consentimiento import ConsentimientoCreate, ConsentimientoRead
from app.services.base_service import BaseService
from app.models.consentimiento import Consentimiento

router = create_router(
    Consentimiento, ConsentimientoCreate, ConsentimientoRead,
    BaseService(Consentimiento), "/consentimientos",
)
