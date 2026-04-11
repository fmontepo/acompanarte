# app/api/permiso_router.py

from app.api.base_router import create_router
from app.schemas.permiso import PermisoCreate, PermisoRead
from app.services.permiso_service import permiso_service

router = create_router(
    None,
    PermisoCreate,
    PermisoRead,
    permiso_service,
    "/permisos"
)