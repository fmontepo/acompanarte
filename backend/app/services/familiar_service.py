# app/services/familiar_service.py
from app.services.base_service import BaseService
from app.models.familiar import Familiar

familiar_service = BaseService(Familiar)