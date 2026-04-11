# app/api/registro_router.py

from app.api.base_router import create_router
from app.schemas.registro import RegistroCreate, RegistroRead
from app.services.registro_service import registro_service

router = create_router(
    None,
    RegistroCreate,
    RegistroRead,
    registro_service,
    "/registros"
)