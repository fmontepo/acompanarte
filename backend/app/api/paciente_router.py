from app.api.base_router import create_router
from app.schemas.paciente import PacienteCreate, PacienteRead
from app.services.base_service import BaseService
from app.models.paciente import Paciente

router = create_router(
    Paciente, PacienteCreate, PacienteRead,
    BaseService(Paciente), "/pacientes",
)
