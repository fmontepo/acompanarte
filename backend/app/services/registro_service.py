# app/services/registro_service.py
from app.services.base_service import BaseService
from app.models.registroSeguimiento import RegistroSeguimiento

registro_service = BaseService(RegistroSeguimiento)