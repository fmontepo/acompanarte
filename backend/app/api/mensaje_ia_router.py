# app/api/mensaje_ia_router.py

from app.api.base_router import create_router
from app.schemas.mensaje_ia import MensajeIACreate, MensajeIARead
from app.services.mensaje_ia_service import mensaje_ia_service

router = create_router(
    None,
    MensajeIACreate,
    MensajeIARead,
    mensaje_ia_service,
    "/mensajes-ia"
)