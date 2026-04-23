# tests/integration/conftest.py
# ─────────────────────────────────────────────────────────────────────────────
# Infraestructura de testing — pool reset por test.
#
# Problema raíz:
#   asyncpg vincula cada conexión al asyncio.Task que la creó.
#   pytest-asyncio corre fixtures y tests en Tasks distintos. El pool
#   estándar recicla conexiones del Task del fixture `seed` al Task de cada
#   test → "Future attached to a different loop".
#
# Solución:
#   Antes de cada test, se llama engine.sync_engine.dispose(close=False).
#   Esto reemplaza el pool por uno vacío nuevo (operación SÍNCRONA, sin I/O
#   async). La primera conexión que necesite el test se crea en su propio
#   Task y nunca hay reciclado.
#
# Por qué sync:
#   dispose(close=False) solo swapea un objeto Python — no cierra conexiones
#   ni hace I/O. Es seguro llamarlo desde un fixture síncrono sin tocar
#   el event loop de pytest-asyncio.
#
# Prerequisito: seed.py de desarrollo debe haber corrido:
#     admin@acompanarte.com     / Admin1234
#     terapeuta@acompanarte.com / Terapeuta1234
#     externo@acompanarte.com   / Externo1234
#     familiar@acompanarte.com  / Familiar1234
#
# Limpieza manual si pytest se interrumpe:
#   DELETE FROM recursos_profesionales WHERE titulo LIKE '[TEST_%]%';
#   DELETE FROM pacientes WHERE nombre_enc LIKE 'PTest_%';
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, text

# ── Path para encontrar el paquete app/ ──────────────────────────────────────
_CANDIDATES = [
    "/app",
    os.path.join(os.path.dirname(__file__), "..", "..", "backend"),
]
for _candidate in _CANDIDATES:
    if os.path.isdir(os.path.join(_candidate, "app")):
        sys.path.insert(0, os.path.abspath(_candidate))
        break

from app.main import app
from app.db.session import AsyncSessionLocal
import app.db.session as db_session_module
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.recursoProfesional import RecursoProfesional

# ID único por corrida para identificar y limpiar los datos de test
RUN_ID = uuid.uuid4().hex[:8]


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURE FUNCIÓN (sync, autouse) — Descarta el pool antes de cada test
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function", autouse=True)
def reset_db_pool():
    """
    Reemplaza el pool de conexiones por uno vacío antes de cada test.

    dispose(close=False): descarta el pool existente y crea uno nuevo vacío.
    Es una operación SÍNCRONA (solo swapea objetos Python, sin I/O).
    La primera conexión del test se crea dentro del Task del test,
    eliminando el "Future attached to a different loop".
    """
    db_session_module.engine.sync_engine.dispose(close=False)
    yield


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURE MÓDULO — Seed: inserta datos, yields IDs, limpia al finalizar
# ─────────────────────────────────────────────────────────────────────────────
@pytest_asyncio.fixture(scope="module")
async def seed():
    """
    Inserta datos mínimos de test en la BD y los commitea.
    Al terminar el módulo, los elimina.
    """
    paciente_id = uuid.uuid4()
    recurso_id  = uuid.uuid4()

    # ── Insertar datos de test ────────────────────────────────────────────────
    async with AsyncSessionLocal() as s:
        ter_int_q = await s.execute(
            select(Usuario).where(Usuario.email == "terapeuta@acompanarte.com")
        )
        ter_int = ter_int_q.scalar_one_or_none()

        s.add(Paciente(
            id=paciente_id,
            nombre_enc=f"PTest_{RUN_ID}",
            apellido_enc=f"ATest_{RUN_ID}",
            activo=True,
        ))
        s.add(RecursoProfesional(
            id=recurso_id,
            titulo=f"[TEST_{RUN_ID}] Recurso pendiente",
            tipo="articulo",
            descripcion="Recurso de test para el widget de validación del dashboard.",
            contenido_texto="Contenido de texto de prueba para el recurso de test.",
            validado=False,
            activo=True,
            subido_por=ter_int.id if ter_int else None,
        ))
        await s.commit()

    yield {
        "paciente_id": paciente_id,
        "recurso_id":  recurso_id,
        "run_id":      RUN_ID,
        "creds": {
            "admin":   ("admin@acompanarte.com",     "Admin1234"),
            "ter-int": ("terapeuta@acompanarte.com", "Terapeuta1234"),
            "ter-ext": ("externo@acompanarte.com",   "Externo1234"),
            "familia": ("familiar@acompanarte.com",  "Familiar1234"),
        },
    }

    # ── Limpiar datos del módulo ──────────────────────────────────────────────
    # Resetear el pool antes del teardown: el último test dejó conexiones
    # vinculadas a su Task — el teardown corre en un Task nuevo.
    db_session_module.engine.sync_engine.dispose(close=False)
    async with AsyncSessionLocal() as s:
        await s.execute(
            text("DELETE FROM actividades_familiar WHERE paciente_id = :pid"),
            {"pid": str(paciente_id)},
        )
        await s.execute(
            text("DELETE FROM recursos_profesionales WHERE id = :rid"),
            {"rid": str(recurso_id)},
        )
        await s.execute(
            text("DELETE FROM pacientes WHERE id = :pid"),
            {"pid": str(paciente_id)},
        )
        await s.commit()


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURE FUNCIÓN — Cliente HTTP
# ─────────────────────────────────────────────────────────────────────────────
@pytest_asyncio.fixture(scope="function")
async def client():
    """
    httpx.AsyncClient con transporte ASGI.
    Cada test obtiene su propio cliente con un pool de DB ya reseteado.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — Obtener token JWT
# ─────────────────────────────────────────────────────────────────────────────
async def get_token(client: AsyncClient, email: str, password: str) -> str:
    """Login vía API y devuelve el access_token."""
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, (
        f"Login falló para '{email}': HTTP {resp.status_code} — {resp.text}\n"
        "¿Está corriendo la BD con los datos del seed.py de desarrollo?"
    )
    return resp.json()["access_token"]
