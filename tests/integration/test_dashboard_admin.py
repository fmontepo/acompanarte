# tests/integration/test_dashboard_admin.py
# Casos cubiertos:
#   CU-AD-01 — GET /api/v1/admin/dashboard devuelve recursos_pendientes
#   CU-AD-02 — POST /api/v1/recursos/{id}/validar → recurso validado, desaparece de pendientes
#
# Requisitos previos: conftest.py con fixture `seed` y `client`.

import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.integration.conftest import get_token


# ─────────────────────────────────────────────────────────────────────────────
# CU-AD-01 · Dashboard admin — recursos_pendientes
# ─────────────────────────────────────────────────────────────────────────────
class TestDashboardAdminPendientes:

    @pytest.mark.asyncio
    async def test_requiere_autenticacion(self, client: AsyncClient):
        """Sin token → 401."""
        resp = await client.get("/api/v1/admin/dashboard")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rol_familia_bloqueado(self, client: AsyncClient, seed: dict):
        """Rol familia → 403 (no tiene acceso al dashboard de admin)."""
        email, password = seed["creds"]["familia"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_ve_recursos_pendientes(self, client: AsyncClient, seed: dict):
        """Admin recibe lista de recursos_pendientes y el recurso de seed está en ella."""
        email, password = seed["creds"]["admin"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert "recursos_pendientes" in data, "La clave 'recursos_pendientes' debe existir en el response"

        pendientes = data["recursos_pendientes"]
        assert isinstance(pendientes, list)

        ids_pendientes = [r["id"] for r in pendientes]
        assert str(seed["recurso_id"]) in ids_pendientes, (
            "El recurso del seed (no validado) debe aparecer en recursos_pendientes"
        )

    @pytest.mark.asyncio
    async def test_pendiente_tiene_campos_requeridos(self, client: AsyncClient, seed: dict):
        """Cada recurso pendiente tiene id, titulo, tipo, descripcion, contenido_texto."""
        email, password = seed["creds"]["admin"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        pendientes = resp.json()["recursos_pendientes"]
        recurso = next((r for r in pendientes if r["id"] == str(seed["recurso_id"])), None)
        assert recurso is not None

        for campo in ("id", "titulo", "tipo", "descripcion", "contenido_texto"):
            assert campo in recurso, f"Falta el campo '{campo}' en el recurso pendiente"


# ─────────────────────────────────────────────────────────────────────────────
# CU-AD-02 · Validar recurso — desaparece de pendientes
# ─────────────────────────────────────────────────────────────────────────────
class TestValidarRecurso:

    @pytest.mark.asyncio
    async def test_sin_auth_retorna_401(self, client: AsyncClient, seed: dict):
        recurso_id = seed["recurso_id"]
        resp = await client.post(f"/api/v1/recursos/{recurso_id}/validar")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rol_familia_no_puede_validar(self, client: AsyncClient, seed: dict):
        email, password = seed["creds"]["familia"]
        token = await get_token(client, email, password)
        recurso_id = seed["recurso_id"]

        resp = await client.post(
            f"/api/v1/recursos/{recurso_id}/validar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_valida_recurso(self, client: AsyncClient, seed: dict):
        """Admin valida el recurso → response con validado=True."""
        email, password = seed["creds"]["admin"]
        token = await get_token(client, email, password)
        recurso_id = seed["recurso_id"]

        resp = await client.post(
            f"/api/v1/recursos/{recurso_id}/validar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["validado"] is True
        assert data["id"] == str(recurso_id)

    @pytest.mark.asyncio
    async def test_recurso_desaparece_de_pendientes(self, client: AsyncClient, seed: dict):
        """Después de validar, el recurso NO debe aparecer en recursos_pendientes del dashboard."""
        email, password = seed["creds"]["admin"]
        token = await get_token(client, email, password)
        recurso_id = seed["recurso_id"]

        # El recurso pudo haberse validado en el test anterior — no volvemos a validar.
        resp = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        pendientes = resp.json()["recursos_pendientes"]
        ids_pendientes = [r["id"] for r in pendientes]
        assert str(recurso_id) not in ids_pendientes, (
            "Un recurso ya validado NO debe aparecer en recursos_pendientes"
        )

    @pytest.mark.asyncio
    async def test_validar_dos_veces_retorna_409(self, client: AsyncClient, seed: dict):
        """Intentar validar un recurso ya validado → 409 Conflict."""
        email, password = seed["creds"]["admin"]
        token = await get_token(client, email, password)
        recurso_id = seed["recurso_id"]

        # Segunda llamada (el recurso ya fue validado en el test anterior)
        resp = await client.post(
            f"/api/v1/recursos/{recurso_id}/validar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_recurso_inexistente_retorna_404(self, client: AsyncClient, seed: dict):
        import uuid
        email, password = seed["creds"]["admin"]
        token = await get_token(client, email, password)

        fake_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/recursos/{fake_id}/validar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
