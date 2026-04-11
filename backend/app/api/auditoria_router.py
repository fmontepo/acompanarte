# app/api/auditoria_router.py

from app.api.base_router import create_router
from app.schemas.auditoria import AuditoriaCreate, AuditoriaRead
from app.services.auditoria_service import auditoria_service

router = create_router(
    None,
    AuditoriaCreate,
    AuditoriaRead,
    auditoria_service,
    "/auditoria"
)