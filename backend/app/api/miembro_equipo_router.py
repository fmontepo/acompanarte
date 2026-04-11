from app.api.base_router import create_router
from app.schemas.miembro_equipo import MiembroEquipoCreate, MiembroEquipoRead
from app.services.base_service import BaseService
from app.models.miembroEquipo import MiembroEquipo

router = create_router(
    MiembroEquipo, MiembroEquipoCreate, MiembroEquipoRead,
    BaseService(MiembroEquipo), "/miembros-equipo",
)
