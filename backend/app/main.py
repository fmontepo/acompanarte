from fastapi import FastAPI

from app.api.usuario_router import router as usuario_router
from app.api.paciente_router import router as paciente_router
from app.api.familiar_router import router as familiar_router
from app.api.terapeuta_router import router as terapeuta_router
from app.api.administrador_router import router as administrador_router
from app.api.vinculo_router import router as vinculo_router
from app.api.parentesco_router import router as parentesco_router
from app.api.equipo_router import router as equipo_router
from app.api.miembro_equipo_router import router as miembro_equipo_router
from app.api.registro_router import router as registro_router
from app.api.permiso_router import router as permiso_router
from app.api.actividad_router import router as actividad_router
from app.api.progreso_router import router as progreso_router
from app.api.sesion_ia_router import router as sesion_ia_router
from app.api.mensaje_ia_router import router as mensaje_ia_router
from app.api.alerta_router import router as alerta_router
from app.api.recurso_router import router as recurso_router
from app.api.consentimiento_router import router as consentimiento_router
from app.api.auditoria_router import router as auditoria_router

app = FastAPI()

app.include_router(usuario_router)
app.include_router(paciente_router)
app.include_router(familiar_router)
app.include_router(terapeuta_router)
app.include_router(administrador_router)
app.include_router(vinculo_router)
app.include_router(parentesco_router)
app.include_router(equipo_router)
app.include_router(miembro_equipo_router)
app.include_router(registro_router)
app.include_router(permiso_router)
app.include_router(actividad_router)
app.include_router(progreso_router)
app.include_router(sesion_ia_router)
app.include_router(mensaje_ia_router)
app.include_router(alerta_router)
app.include_router(recurso_router)
app.include_router(consentimiento_router)
app.include_router(auditoria_router)
