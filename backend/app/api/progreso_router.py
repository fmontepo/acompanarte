from app.api.base_router import create_router
from app.schemas.progreso_actividad import ProgresoActividadCreate, ProgresoActividadRead
from app.services.base_service import BaseService
from app.models.progresoActividad import ProgresoActividad

router = create_router(
    ProgresoActividad, ProgresoActividadCreate, ProgresoActividadRead,
    BaseService(ProgresoActividad), "/progreso",
)
