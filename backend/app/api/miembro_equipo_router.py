# app/api/miembro_equipo_router.py

from app.api.base_router import create_router
from app.schemas.miembroEquipo import MiembroEquipoCreate, MiembroEquipoRead
from app.services.miembro_equipo_service import miembro_equipo_service

router = create_router(
    None,
    MiembroEquipoCreate,
    MiembroEquipoRead,
    miembro_equipo_service,
    "/miembros-equipo"
)