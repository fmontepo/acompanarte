# app/services/paciente_service.py
from app.services.base_service import BaseService
from app.models.paciente import Paciente

paciente_service = BaseService(Paciente)