from app.api.base_router import create_router
from app.schemas.paciente import PacienteCreate, PacienteRead
from app.services.paciente_service import paciente_service

router = create_router(
    None,
    PacienteCreate,
    PacienteRead,
    paciente_service,
    "/pacientes"
)