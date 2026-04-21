# app/services/vinculo_service.py
from app.services.base_service import BaseService
from app.models.vinculoPaciente import VinculoPaciente

vinculo_service = BaseService(VinculoPaciente)