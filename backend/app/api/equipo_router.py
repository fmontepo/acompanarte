from app.api.base_router import create_router
from app.schemas.equipo_terapeutico import EquipoTerapeuticoCreate, EquipoTerapeuticoRead
from app.services.base_service import BaseService
from app.models.equipoTerapeutico import EquipoTerapeutico

router = create_router(
    EquipoTerapeutico, EquipoTerapeuticoCreate, EquipoTerapeuticoRead,
    BaseService(EquipoTerapeutico), "/equipos",
)
