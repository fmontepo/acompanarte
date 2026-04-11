# app/api/recurso_router.py

from app.api.base_router import create_router
from app.schemas.recurso import RecursoCreate, RecursoRead
from app.services.recurso_service import recurso_service

router = create_router(
    None,
    RecursoCreate,
    RecursoRead,
    recurso_service,
    "/recursos"
)