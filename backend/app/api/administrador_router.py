# app/api/administrador_router.py

from app.api.base_router import create_router
from app.schemas.administrador import AdministradorCreate, AdministradorRead
from app.services.administrador_service import administrador_service

router = create_router(
    None,
    AdministradorCreate,
    AdministradorRead,
    administrador_service,
    "/administradores"
)