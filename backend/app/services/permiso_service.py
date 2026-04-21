# app/services/permiso_service.py
from app.services.base_service import BaseService
from app.models.permisoSeguimiento import PermisoSeguimiento

permiso_service = BaseService(PermisoSeguimiento)