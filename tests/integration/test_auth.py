# tests/integration/test_auth.py
# Casos cubiertos:
#   CU-PUB-01 — Login con credenciales válidas → token JWT válido + default_path correcto por rol
#   CU-PUB-02 — Credenciales inválidas → 401, sin token
#   CU-PUB-05 — Rutas protegidas sin token → 401
#   CU-PUB-06 — Rutas con rol incorrecto → 403
#
# Patrón aplicado:
#   - reset_db_pool (autouse) descarta el pool antes de cada test
#   - seed (module) provee credenciales; el reset en teardown evita "Future attached to a different loop"
#   - client (function) es un httpx.AsyncClient con ASGITransport (sin servidor HTTP)
#   - get_token es el helper de conftest — no duplicar lógica de login

import pytest
from httpx import AsyncClient

from tests.integration.conftest import get_token


# ─────────────────────────────────────────────────────────────────────────────
# CU-PUB-01 · Login con credenciales válidas — token y estructura del response
# ─────────────────────────────────────────────────────────────────────────────
class TestLoginValido:

    async def test_login_admin_retorna_token(self, client: AsyncClient, seed: dict):
        """Admin: login correcto → 200, access_token presente."""
        email, password = seed["creds"]["admin"]
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data, "Debe retornar access_token"
        assert data["token_type"] == "bearer"

    async def test_login_admin_default_path_correcto(self, client: AsyncClient, seed: dict):
        """Admin: el default_path en el response debe ser /admin/dashboard."""
        email, password = seed["creds"]["admin"]
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        user = resp.json()["user"]
        assert user["rol_key"] == "admin"
        assert "/admin" in user["default_path"], (
            f"default_path del admin debe apuntar a /admin, se obtuvo: {user['default_path']}"
        )

    async def test_login_terapeuta_interno_retorna_token(self, client: AsyncClient, seed: dict):
        """Terapeuta interno: login correcto → 200, rol_key correcto."""
        email, password = seed["creds"]["ter-int"]
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["rol_key"] == "ter-int"

    async def test_login_familiar_retorna_token(self, client: AsyncClient, seed: dict):
        """Familiar: login correcto → 200, rol_key correcto."""
        email, password = seed["creds"]["familia"]
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["rol_key"] == "familia"

    async def test_login_response_tiene_campos_requeridos(self, client: AsyncClient, seed: dict):
        """El response de login debe incluir id, email, nombre, rol_key, default_path, nav_config."""
        email, password = seed["creds"]["ter-int"]
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        user = resp.json()["user"]
        for campo in ("id", "email", "nombre", "rol_key", "default_path", "nav_config"):
            assert campo in user, f"Falta el campo '{campo}' en el response de login"


# ─────────────────────────────────────────────────────────────────────────────
# CU-PUB-02 · Credenciales inválidas → 401
# ─────────────────────────────────────────────────────────────────────────────
class TestLoginInvalido:

    async def test_email_inexistente_retorna_401(self, client: AsyncClient):
        """Email que no existe en la BD → 401."""
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "noexiste@acompanarte.com", "password": "CualquierPass1"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401

    async def test_contrasena_incorrecta_retorna_401(self, client: AsyncClient, seed: dict):
        """Email correcto pero contraseña equivocada → 401."""
        email, _ = seed["creds"]["admin"]
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "ContrasenaErronea999!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401

    async def test_contrasena_incorrecta_no_retorna_token(self, client: AsyncClient, seed: dict):
        """Credenciales inválidas → el body NO debe contener access_token."""
        email, _ = seed["creds"]["ter-int"]
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "WrongPassword123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401
        assert "access_token" not in resp.json()

    async def test_sin_datos_retorna_422(self, client: AsyncClient):
        """Body vacío → FastAPI valida el form y retorna 422 Unprocessable Entity."""
        resp = await client.post(
            "/api/v1/auth/login",
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# CU-PUB-05 · /auth/me — rutas protegidas sin token → 401
# ─────────────────────────────────────────────────────────────────────────────
class TestMeEndpoint:

    async def test_me_sin_token_retorna_401(self, client: AsyncClient):
        """/auth/me sin Authorization header → 401."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_con_token_invalido_retorna_401(self, client: AsyncClient):
        """/auth/me con token malformado → 401."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer estoNoEsUnToken"},
        )
        assert resp.status_code == 401

    async def test_me_con_token_valido_retorna_datos(self, client: AsyncClient, seed: dict):
        """/auth/me con token válido → 200 con datos del usuario."""
        email, password = seed["creds"]["admin"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == email
        assert data["rol"] == "admin"

    async def test_me_terapeuta_retorna_rol_correcto(self, client: AsyncClient, seed: dict):
        """/auth/me con token de ter-ext → rol == 'ter-ext'."""
        email, password = seed["creds"]["ter-ext"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["rol"] == "ter-ext"


# ─────────────────────────────────────────────────────────────────────────────
# CU-PUB-06 · Rutas con rol incorrecto → 403
# ─────────────────────────────────────────────────────────────────────────────
class TestAccesoRolIncorrecto:

    async def test_familiar_no_accede_a_admin_dashboard(self, client: AsyncClient, seed: dict):
        """Token familiar → GET /admin/dashboard retorna 403."""
        email, password = seed["creds"]["familia"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_familiar_no_puede_listar_actividades(self, client: AsyncClient, seed: dict):
        """Token familiar → GET /actividades/ retorna 403 (solo terapeutas)."""
        email, password = seed["creds"]["familia"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/actividades/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_terapeuta_externo_no_accede_a_admin_dashboard(self, client: AsyncClient, seed: dict):
        """Token ter-ext → GET /admin/dashboard retorna 403."""
        email, password = seed["creds"]["ter-ext"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
