from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine
from app.db.base import Base

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
from app.api.auth_router import router as auth_router


# ---------------------------------------------------------------------------
# Lifespan: se ejecuta al iniciar y al apagar la aplicación
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: crear tablas si no existen (solo desarrollo)
    # En producción usar: alembic upgrade head
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: liberar el pool de conexiones
    await engine.dispose()


# ---------------------------------------------------------------------------
# Aplicación principal
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Acompañarte API",
    description=(
        "Plataforma de acompañamiento para familias con TEA. "
        "IA local · Datos sensibles protegidos · Ley 25.326"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — permite comunicación con el frontend React
# En producción restringir origins a la IP/dominio real del cliente
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — todos bajo /api/v1/ según contrato de arquitectura
# ---------------------------------------------------------------------------
PREFIX = "/api/v1"

app.include_router(auth_router,            prefix=PREFIX)
app.include_router(usuario_router,         prefix=PREFIX)
app.include_router(paciente_router,        prefix=PREFIX)
app.include_router(familiar_router,        prefix=PREFIX)
app.include_router(terapeuta_router,       prefix=PREFIX)
app.include_router(administrador_router,   prefix=PREFIX)
app.include_router(vinculo_router,         prefix=PREFIX)
app.include_router(parentesco_router,      prefix=PREFIX)
app.include_router(equipo_router,          prefix=PREFIX)
app.include_router(miembro_equipo_router,  prefix=PREFIX)
app.include_router(registro_router,        prefix=PREFIX)
app.include_router(permiso_router,         prefix=PREFIX)
app.include_router(actividad_router,       prefix=PREFIX)
app.include_router(progreso_router,        prefix=PREFIX)
app.include_router(sesion_ia_router,       prefix=PREFIX)
app.include_router(mensaje_ia_router,      prefix=PREFIX)
app.include_router(alerta_router,          prefix=PREFIX)
app.include_router(recurso_router,         prefix=PREFIX)
app.include_router(consentimiento_router,  prefix=PREFIX)
app.include_router(auditoria_router,       prefix=PREFIX)
app.include_router(auth_router,            prefix=PREFIX)

# ---------------------------------------------------------------------------
# Health check — para Docker y monitoreo
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
