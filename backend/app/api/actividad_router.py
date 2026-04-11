from app.api.base_router import create_router
from app.schemas.actividad_familiar import ActividadFamiliarCreate, ActividadFamiliarRead
from app.services.base_service import BaseService
from app.models.actividadFamiliar import ActividadFamiliar

router = create_router(
    ActividadFamiliar, ActividadFamiliarCreate, ActividadFamiliarRead,
    BaseService(ActividadFamiliar), "/actividades",
)
