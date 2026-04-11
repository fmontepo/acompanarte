from app.api.base_router import create_router
from app.schemas.familiar import FamiliarCreate, FamiliarRead
from app.services.base_service import BaseService
from app.models.familiar import Familiar

router = create_router(
    Familiar, FamiliarCreate, FamiliarRead,
    BaseService(Familiar), "/familiares",
)
