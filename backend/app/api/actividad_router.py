# app/api/actividad_router.py

from app.api.base_router import create_router
from app.schemas.actividad import ActividadCreate, ActividadRead
from app.services.actividadFamiliar_service import actividadFamiliar_service

router = create_router(
    None,
    ActividadCreate,
    ActividadRead,
    actividadFamiliar_service,
    "/actividades"
)