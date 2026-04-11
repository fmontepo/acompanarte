from app.api.base_router import create_router
from app.schemas.administrador import AdministradorCreate, AdministradorRead
from app.services.base_service import BaseService
from app.models.administrador import Administrador

router = create_router(
    Administrador, AdministradorCreate, AdministradorRead,
    BaseService(Administrador), "/administradores",
)
