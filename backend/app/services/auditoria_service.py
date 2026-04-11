# app/services/auditoria_service.py
from app.services.base_service import BaseService
from app.models.auditoria import Auditoria

auditoria_service = BaseService(Auditoria)