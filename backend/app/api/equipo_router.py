# app/api/equipo_router.py

from app.api.base_router import create_router
from app.schemas.equipo import EquipoCreate, EquipoRead
from app.services.equipoTerapeutico_service import equipoTerapeutico_service
router = create_router(
    None,
    EquipoCreate,
    EquipoRead,
    equipoTerapeutico_service,
    "/equipos"
)