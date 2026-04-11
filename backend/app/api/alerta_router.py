# app/api/alerta_router.py

from app.api.base_router import create_router
from app.schemas.alerta import AlertaCreate, AlertaRead
from app.services.alerta_service import alerta_service

router = create_router(
    None,
    AlertaCreate,
    AlertaRead,
    alerta_service,
    "/alertas"
)