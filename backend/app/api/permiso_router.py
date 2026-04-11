from app.api.base_router import create_router
from app.schemas.permiso_seguimiento import PermisoSeguimientoCreate, PermisoSeguimientoRead
from app.services.base_service import BaseService
from app.models.permisoSeguimiento import PermisoSeguimiento

router = create_router(
    PermisoSeguimiento, PermisoSeguimientoCreate, PermisoSeguimientoRead,
    BaseService(PermisoSeguimiento), "/permisos",
)
