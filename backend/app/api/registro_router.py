from app.api.base_router import create_router
from app.schemas.registro_seguimiento import RegistroSeguimientoCreate, RegistroSeguimientoRead
from app.services.base_service import BaseService
from app.models.registroSeguimiento import RegistroSeguimiento

router = create_router(
    RegistroSeguimiento, RegistroSeguimientoCreate, RegistroSeguimientoRead,
    BaseService(RegistroSeguimiento), "/registros",
)
