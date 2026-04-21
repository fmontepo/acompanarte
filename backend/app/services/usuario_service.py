# app/services/usuario_service.py
from app.services.base_service import BaseService
from app.models.usuario import Usuario

usuario_service = BaseService(Usuario)