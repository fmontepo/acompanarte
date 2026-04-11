# app/api/usuario_router.py
from app.api.base_router import create_router
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.services.usuario_service import usuario_service

router = create_router(
    model=None,
    schema_create=UsuarioCreate,
    schema_read=UsuarioRead,
    service=usuario_service,
    prefix="/usuarios"
)