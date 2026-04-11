# app/api/progreso_router.py

from app.api.base_router import create_router
from app.schemas.progreso import ProgresoCreate, ProgresoRead
from app.services.progreso_service import progreso_service

router = create_router(
    None,
    ProgresoCreate,
    ProgresoRead,
    progreso_service,
    "/progreso"
)