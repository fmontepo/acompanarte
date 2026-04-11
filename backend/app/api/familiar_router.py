from app.api.base_router import create_router
from app.schemas.familiar import FamiliarCreate, FamiliarRead
from app.services.familiar_service import familiar_service

router = create_router(
    None,
    FamiliarCreate,
    FamiliarRead,
    familiar_service,
    "/familiares"
)