from app.api.base_router import create_router
from app.schemas.vinculo_paciente import VinculoPacienteCreate, VinculoPacienteRead
from app.services.base_service import BaseService
from app.models.vinculoPaciente import VinculoPaciente

router = create_router(
    VinculoPaciente, VinculoPacienteCreate, VinculoPacienteRead,
    BaseService(VinculoPaciente), "/vinculos",
)
