# tests/integration/test_rag_clinico.py
# ─────────────────────────────────────────────────────────────────────────────
# Tests de INTEGRACIÓN para el RAG clínico interno.
# Requieren la BD activa con datos del seed.py de desarrollo.
#
# Para tests unitarios (sin BD) ver: tests/unit/test_rag_clinico_unit.py
#
# Casos de uso cubiertos:
#   UC-RAG-10  endpoint acceso  — control de roles /batch/embedding
#   UC-RAG-09  filtro pacientes — buscar_contexto acota por pacientes del terapeuta
# ─────────────────────────────────────────────────────────────────────────────

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from tests.integration.conftest import get_token


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-10 · Control de acceso — endpoint /batch/embedding
# ─────────────────────────────────────────────────────────────────────────────

class TestBatchEndpointAcceso:
    """POST /api/v1/ia/terapeuta/batch/embedding requiere rol ter-int o admin."""

    @pytest.mark.asyncio
    async def test_sin_token_retorna_401(self, client: AsyncClient, seed: dict):
        resp = await client.post("/api/v1/ia/terapeuta/batch/embedding")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rol_familia_retorna_403(self, client: AsyncClient, seed: dict):
        email, password = seed["creds"]["familia"]
        token = await get_token(client, email, password)

        resp = await client.post(
            "/api/v1/ia/terapeuta/batch/embedding",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_rol_ter_ext_retorna_403(self, client: AsyncClient, seed: dict):
        email, password = seed["creds"]["ter-ext"]
        token = await get_token(client, email, password)

        resp = await client.post(
            "/api/v1/ia/terapeuta/batch/embedding",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_rol_ter_int_puede_ejecutar_batch(self, client: AsyncClient, seed: dict):
        """ter-int recibe 200 con stats del batch (batch mockeado para no requerir modelo)."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        stats_mock = {
            "inicio": "2025-01-01T00:00:00+00:00",
            "registros_actualizados": 0,
            "actividades_actualizadas": 0,
            "progresos_actualizados": 0,
            "errores": [],
            "duracion_seg": 0.1,
        }

        with patch(
            "app.services.scheduler.trigger_manual",
            new_callable=AsyncMock,
            return_value=stats_mock,
        ):
            resp = await client.post(
                "/api/v1/ia/terapeuta/batch/embedding",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "mensaje" in data
        assert "stats" in data
        assert data["stats"]["errores"] == []

    @pytest.mark.asyncio
    async def test_rol_admin_puede_ejecutar_batch(self, client: AsyncClient, seed: dict):
        """admin recibe 200 con stats del batch."""
        email, password = seed["creds"]["admin"]
        token = await get_token(client, email, password)

        stats_mock = {
            "inicio": "2025-01-01T00:00:00+00:00",
            "registros_actualizados": 3,
            "actividades_actualizadas": 1,
            "progresos_actualizados": 0,
            "errores": [],
            "duracion_seg": 1.5,
        }

        with patch(
            "app.services.scheduler.trigger_manual",
            new_callable=AsyncMock,
            return_value=stats_mock,
        ):
            resp = await client.post(
                "/api/v1/ia/terapeuta/batch/embedding",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["registros_actualizados"] == 3

    @pytest.mark.asyncio
    async def test_respuesta_incluye_campo_mensaje_y_stats(self, client: AsyncClient, seed: dict):
        """El cuerpo de la respuesta tiene la estructura esperada."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        stats_mock = {
            "inicio": "2025-01-01T00:00:00+00:00",
            "registros_actualizados": 0,
            "actividades_actualizadas": 0,
            "progresos_actualizados": 0,
            "errores": [],
            "duracion_seg": 0.0,
        }

        with patch(
            "app.services.scheduler.trigger_manual",
            new_callable=AsyncMock,
            return_value=stats_mock,
        ):
            resp = await client.post(
                "/api/v1/ia/terapeuta/batch/embedding",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        # Verificar estructura completa de la respuesta
        assert set(data.keys()) >= {"mensaje", "stats"}
        stats = data["stats"]
        assert "registros_actualizados" in stats
        assert "actividades_actualizadas" in stats
        assert "progresos_actualizados" in stats
        assert "errores" in stats
        assert "duracion_seg" in stats


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-09 · Filtrado de pacientes — stats endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestStatsEndpointAcceso:
    """GET /api/v1/ia/terapeuta/stats también requiere rol ter-int o admin."""

    @pytest.mark.asyncio
    async def test_sin_token_retorna_401(self, client: AsyncClient, seed: dict):
        resp = await client.get("/api/v1/ia/terapeuta/stats")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rol_familia_retorna_403(self, client: AsyncClient, seed: dict):
        email, password = seed["creds"]["familia"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/ia/terapeuta/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_rol_ter_ext_retorna_403(self, client: AsyncClient, seed: dict):
        email, password = seed["creds"]["ter-ext"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/ia/terapeuta/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_rol_ter_int_accede_a_stats(self, client: AsyncClient, seed: dict):
        """ter-int puede acceder a sus propias estadísticas."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        resp = await client.get(
            "/api/v1/ia/terapeuta/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        # El terapeuta puede no tener pacientes en el seed básico, pero la respuesta es válida
        assert resp.status_code == 200
        data = resp.json()
        assert "total_pacientes" in data
        assert "diagnosticos" in data
        assert "bienestar_promedio" in data
        assert "registros_tipos" in data
        assert "actividades_efectividad" in data
        assert "evolucion_bienestar" in data
