from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.models.rol import Rol
from app.models.contacto_publico import ContactoPublico  # noqa: F401 — necesario para create_all
from app.models.regla_ia import ReglaIA                  # noqa: F401 — necesario para create_all
from app.models.parentesco import Parentesco              # noqa: F401 — necesario para create_all

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
from app.api.sesion_ia_router import router as sesion_ia_router, reglas_router
from app.api.mensaje_ia_router import router as mensaje_ia_router
from app.api.alerta_router import router as alerta_router
from app.api.recurso_router import router as recurso_router
from app.api.consentimiento_router import router as consentimiento_router
from app.api.auditoria_router import router as auditoria_router
from app.api.dashboard_router import router as dashboard_router
from app.api.auth_router import router as auth_router
from app.api.contacto_publico_router import router as contacto_publico_router
from app.api.contacto_publico_router import terapeutas_router as contacto_terapeutas_router
from app.api.regla_ia_router import router as regla_ia_router
from app.api.terapeuta_ia_router import router as terapeuta_ia_router


# ---------------------------------------------------------------------------
# Lifespan: se ejecuta al iniciar y al apagar la aplicación
# ---------------------------------------------------------------------------
_ROLES_SEED = [
    {
        "key": "familia",
        "label": "Panel familiar",
        "default_path": "/familiar/dashboard",
        "nav_config": [
            {"section": "Principal", "items": [
                {"id": "dashboard",     "icon": "home",      "label": "Panel de inicio"},
                {"id": "mis-parientes", "icon": "users",     "label": "Mis parientes"},
                {"id": "seguimientos",  "icon": "clipboard", "label": "Seguimientos"},
                {"id": "actividades",   "icon": "target",    "label": "Actividades"},
            ]},
            {"section": "Herramientas", "items": [
                {"id": "asistente", "icon": "bot",  "label": "Asistente IA"},
                {"id": "alertas",   "icon": "bell", "label": "Alertas", "badge": 0},
            ]},
        ],
    },
    {
        "key": "ter-int",
        "label": "Terapeuta interno",
        "default_path": "/terapeuta/interno/dashboard",
        "nav_config": [
            {"section": "Principal", "items": [
                {"id": "ter-int-dash",        "icon": "home",      "label": "Panel de inicio"},
                {"id": "ter-int-pacientes",   "icon": "users",     "label": "Pacientes"},
                {"id": "ter-int-registros",   "icon": "pencil",    "label": "Registros"},
                {"id": "ter-int-actividades", "icon": "clipboard", "label": "Actividades"},
            ]},
            {"section": "Herramientas", "items": [
                {"id": "ter-int-asistente",    "icon": "bot",  "label": "Asistente IA"},
                {"id": "ter-int-conocimiento", "icon": "book", "label": "Base de conocimiento"},
                {"id": "alertas",              "icon": "bell", "label": "Alertas", "badge": 0},
            ]},
        ],
    },
    {
        "key": "ter-ext",
        "label": "Terapeuta externo",
        "default_path": "/terapeuta/externo/dashboard",
        "nav_config": [
            {"section": "Principal", "items": [
                {"id": "ter-ext-dash",      "icon": "home",   "label": "Panel de inicio"},
                {"id": "ter-ext-registros", "icon": "pencil", "label": "Mis registros"},
            ]},
        ],
    },
    {
        "key": "admin",
        "label": "Administración",
        "default_path": "/admin/dashboard",
        "nav_config": [
            {"section": "Sistema", "items": [
                {"id": "admin-dash",      "icon": "home",      "label": "Panel de inicio"},
                {"id": "admin-usuarios",  "icon": "users",     "label": "Usuarios"},
                {"id": "admin-contactos", "icon": "mail",       "label": "Contactos TEA"},
                {"id": "admin-reglas",    "icon": "shield",     "label": "Reglas IA"},
                {"id": "admin-auditoria", "icon": "bar-chart",  "label": "Auditoría"},
            ]},
        ],
    },
]


_REGLAS_SEED = [
    # ── Reglas positivas — contexto familiar ────────────────────────────────
    {"tipo": "positiva", "orden": 1, "contexto": "familiar",
     "texto": "Orientar sobre señales tempranas del Trastorno del Espectro Autista (TEA) en niños",
     "descripcion": "Tema central del asistente familiar"},
    {"tipo": "positiva", "orden": 2, "contexto": "familiar",
     "texto": "Informar sobre estrategias de comunicación y apoyo para familias con niños en el espectro",
     "descripcion": "Apoyo familiar"},
    {"tipo": "positiva", "orden": 3, "contexto": "familiar",
     "texto": "Explicar qué es el TEA, sus niveles y cómo impacta en el desarrollo infantil",
     "descripcion": "Educación sobre TEA"},
    {"tipo": "positiva", "orden": 4, "contexto": "familiar",
     "texto": "Orientar sobre cuándo y cómo buscar una evaluación diagnóstica con especialistas",
     "descripcion": "Derivación a profesionales"},
    {"tipo": "positiva", "orden": 5, "contexto": "familiar",
     "texto": "Describir actividades y ejercicios de estimulación adaptados al nivel TEA, basados en bibliografía validada",
     "descripcion": "Actividades prácticas"},
    {"tipo": "positiva", "orden": 6, "contexto": "familiar",
     "texto": "Contener emocionalmente a familias y cuidadores, reconociendo el esfuerzo que implica acompañar a un niño con TEA",
     "descripcion": "Apoyo emocional"},
    # ── Reglas positivas — contexto terapeuta ───────────────────────────────
    {"tipo": "positiva", "orden": 1, "contexto": "terapeuta",
     "texto": "Analizar tendencias y patrones en el historial clínico de los pacientes",
     "descripcion": "Análisis clínico"},
    {"tipo": "positiva", "orden": 2, "contexto": "terapeuta",
     "texto": "Sugerir estrategias terapéuticas basadas en la bibliografía validada del sistema",
     "descripcion": "Recomendaciones basadas en evidencia"},
    {"tipo": "positiva", "orden": 3, "contexto": "terapeuta",
     "texto": "Identificar patrones de progreso, estancamiento o regresión en los pacientes",
     "descripcion": "Seguimiento de evolución"},
    {"tipo": "positiva", "orden": 4, "contexto": "terapeuta",
     "texto": "Comparar efectividad de actividades entre pacientes con diagnósticos similares",
     "descripcion": "Análisis comparativo de actividades"},
    {"tipo": "positiva", "orden": 5, "contexto": "terapeuta",
     "texto": "Responder consultas sobre el historial de registros, bienestar y actividades de los pacientes asignados",
     "descripcion": "Consultas sobre pacientes propios"},
    # ── Reglas negativas — globales (aplican a familiar Y terapeuta) ─────────
    {"tipo": "negativa", "orden": 1, "contexto": "global",
     "texto": "Emitir diagnósticos definitivos ni afirmar que un paciente tiene o no tiene una condición específica",
     "descripcion": "Restricción diagnóstica — no negociable"},
    {"tipo": "negativa", "orden": 2, "contexto": "global",
     "texto": "Recomendar medicamentos, suplementos ni tratamientos farmacológicos específicos",
     "descripcion": "Sin recomendaciones médicas"},
    {"tipo": "negativa", "orden": 3, "contexto": "global",
     "texto": "Dar información que contradiga o no esté respaldada por la bibliografía validada cargada en el sistema",
     "descripcion": "Integridad de fuentes"},
    # ── Reglas negativas — contexto familiar ────────────────────────────────
    {"tipo": "negativa", "orden": 4, "contexto": "familiar",
     "texto": "Responder sobre temas ajenos al neurodesarrollo, TEA, apoyo familiar o desarrollo infantil",
     "descripcion": "Mantener el foco temático"},
    {"tipo": "negativa", "orden": 5, "contexto": "familiar",
     "texto": "Minimizar ni invalidar las preocupaciones de los familiares — siempre tomarlas en serio",
     "descripcion": "Respeto a la familia"},
    {"tipo": "negativa", "orden": 6, "contexto": "familiar",
     "texto": "Asumir o afirmar el nivel de funcionamiento de un niño sin evaluación profesional",
     "descripcion": "Sin clasificación sin base clínica"},
    # ── Reglas negativas — contexto terapeuta ───────────────────────────────
    {"tipo": "negativa", "orden": 4, "contexto": "terapeuta",
     "texto": "Revelar datos identificatorios de los pacientes — siempre usar referencias anónimas (Paciente 1, Paciente 2)",
     "descripcion": "Protección de datos clínicos"},
    {"tipo": "negativa", "orden": 5, "contexto": "terapeuta",
     "texto": "Responder consultas sobre pacientes que no estén asignados al terapeuta autenticado",
     "descripcion": "Restricción de acceso por paciente"},
]


async def _seed_roles():
    """
    Sincroniza los roles con _ROLES_SEED en cada arranque.
    - Crea los roles que no existan.
    - Actualiza nav_config, label y default_path de los existentes.
    Esto garantiza que los cambios de nav en el código se apliquen
    sin necesidad de borrar la tabla.
    """
    from sqlalchemy.orm.attributes import flag_modified
    async with AsyncSessionLocal() as session:
        for r_data in _ROLES_SEED:
            result = await session.execute(select(Rol).where(Rol.key == r_data["key"]))
            rol = result.scalar_one_or_none()
            if rol is None:
                session.add(Rol(
                    key=r_data["key"],
                    label=r_data["label"],
                    default_path=r_data["default_path"],
                    nav_config=r_data["nav_config"],
                ))
            else:
                # Sincronizar siempre — recoge cualquier cambio en el código
                rol.label        = r_data["label"]
                rol.default_path = r_data["default_path"]
                rol.nav_config   = r_data["nav_config"]
                flag_modified(rol, "nav_config")
        await session.commit()


async def _seed_parentescos():
    """Inserta los tipos de parentesco si la tabla está vacía. Idempotente."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Parentesco))
        if result.scalars().first() is not None:
            return  # ya sembrado
        parentescos = [
            ("MA", "Madre"),
            ("PA", "Padre"),
            ("AB", "Abuelo/a"),
            ("TI", "Tío/a"),
            ("HE", "Hermano/a"),
            ("TU", "Tutor legal"),
            ("OT", "Otro"),
        ]
        for id_p, nombre in parentescos:
            session.add(Parentesco(id_parentesco=id_p, nombre=nombre))
        await session.commit()


async def _seed_reglas_ia():
    """Inserta las reglas de IA por defecto si la tabla está vacía. Idempotente."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ReglaIA))
        if result.scalars().first() is not None:
            return  # ya hay reglas — no sobreescribir cambios del admin
        for r in _REGLAS_SEED:
            session.add(ReglaIA(
                tipo=r["tipo"],
                orden=r["orden"],
                contexto=r.get("contexto", "global"),
                texto=r["texto"],
                descripcion=r.get("descripcion"),
                activa=True,
            ))
        await session.commit()


async def _migrate():
    """Migraciones incrementales — idempotentes, seguras en cada arranque."""
    from sqlalchemy import text
    async with engine.begin() as conn:
        # v2: campo contexto en reglas_ia (familiar | terapeuta | global)
        await conn.execute(text(
            "ALTER TABLE reglas_ia ADD COLUMN IF NOT EXISTS "
            "contexto VARCHAR(15) NOT NULL DEFAULT 'global'"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_reglas_ia_contexto ON reglas_ia(contexto)"
        ))
        # v3: etapas en actividades y progreso
        await conn.execute(text(
            "ALTER TABLE actividades_familiar ADD COLUMN IF NOT EXISTS "
            "total_etapas INTEGER NOT NULL DEFAULT 1"
        ))
        await conn.execute(text(
            "ALTER TABLE progreso_actividad ADD COLUMN IF NOT EXISTS "
            "es_completada BOOLEAN NOT NULL DEFAULT TRUE"
        ))
        await conn.execute(text(
            "ALTER TABLE progreso_actividad ADD COLUMN IF NOT EXISTS "
            "etapas_completadas INTEGER"
        ))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: crear tablas si no existen (solo desarrollo)
    # En producción usar: alembic upgrade head
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Migraciones incrementales
    await _migrate()
    # Seed roles iniciales si la tabla está vacía
    await _seed_roles()
    await _seed_reglas_ia()
    await _seed_parentescos()
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
app.include_router(reglas_router,          prefix=PREFIX)
app.include_router(mensaje_ia_router,      prefix=PREFIX)
app.include_router(alerta_router,          prefix=PREFIX)
app.include_router(recurso_router,         prefix=PREFIX)
app.include_router(consentimiento_router,  prefix=PREFIX)
app.include_router(auditoria_router,       prefix=PREFIX)
app.include_router(dashboard_router,              prefix=PREFIX)
app.include_router(contacto_publico_router,       prefix=PREFIX)
app.include_router(contacto_terapeutas_router,    prefix=PREFIX)
app.include_router(regla_ia_router,               prefix=PREFIX)
app.include_router(terapeuta_ia_router,           prefix=PREFIX)
# auth_router ya incluido al inicio — no duplicar

# ---------------------------------------------------------------------------
# Health check — para Docker y monitoreo
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
