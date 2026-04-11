from app.api.base_router import create_router
from app.schemas.terapeuta import TerapeutaCreate, TerapeutaRead
from app.services.base_service import BaseService
from app.models.terapeuta import Terapeuta

router = create_router(
    Terapeuta, TerapeutaCreate, TerapeutaRead,
    BaseService(Terapeuta), "/terapeutas",
)
