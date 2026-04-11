# app/api/sesion_ia_router.py

from app.api.base_router import create_router
from app.schemas.sesion_ia import SesionIACreate, SesionIARead
from app.services.sesion_ia_service import sesion_ia_service

router = create_router(
    None,
    SesionIACreate,
    SesionIARead,
    sesion_ia_service,
    "/sesiones-ia"
)