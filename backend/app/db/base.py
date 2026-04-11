# app/db/base.py
# Base declarativa compartida por todos los modelos.
# TODOS los modelos deben importarse aquí para que Alembic los detecte
# al generar migraciones con: alembic revision --autogenerate

from sqlalchemy.orm import declarative_base
Base = declarative_base()

# ---------------------------------------------------------------------------
# Importar todos los modelos — NO comentar ninguno
# ---------------------------------------------------------------------------
# Tablas de referencia (sin dependencias)
from app.models.provincia import Provincia                      # noqa: F401
from app.models.localidad import Localidad                      # noqa: F401
from app.models.parentesco import Parentesco                    # noqa: F401
from app.models.diagnostico import Diagnostico                  # noqa: F401

# Usuarios y roles
from app.models.rol import Rol                                  # noqa: F401
from app.models.usuario import Usuario                          # noqa: F401
from app.models.administrador import Administrador              # noqa: F401
from app.models.familiar import Familiar                        # noqa: F401
from app.models.terapeuta import Terapeuta                      # noqa: F401


# Consentimiento
from app.models.consentimiento import Consentimiento            # noqa: F401

# Pacientes y vínculos
from app.models.paciente import Paciente                        # noqa: F401
from app.models.vinculoPaciente import VinculoPaciente          # noqa: F401

# Equipos terapéuticos
from app.models.equipoTerapeutico import EquipoTerapeutico      # noqa: F401
from app.models.miembroEquipo import MiembroEquipo              # noqa: F401

# Seguimiento clínico
from app.models.registroSeguimiento import RegistroSeguimiento  # noqa: F401
from app.models.permisoSeguimiento import PermisoSeguimiento    # noqa: F401

# Actividades y progreso
from app.models.actividadFamiliar import ActividadFamiliar      # noqa: F401
from app.models.progresoActividad import ProgresoActividad      # noqa: F401

# Módulo IA
from app.models.ia import SesionIA, MensajeIA                   # noqa: F401
from app.models.alerta import Alerta                            # noqa: F401

# Recursos y auditoría
from app.models.recursoProfesional import RecursoProfesional    # noqa: F401
from app.models.auditoria import EventoAuditoria                # noqa: F401
