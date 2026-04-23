# tests/integration/test_actividades.py
# Casos cubiertos:
#   CU-TI-03 — Crear actividad con N etapas → total_etapas == N (regresión del fix)
#   CU-TI-04 — Asignar actividad a paciente → aparece en GET del familiar
#
# Requisitos previos: conftest.py con fixture `seed` y `client`.

import pytest
import uuid
from httpx import AsyncClient

from tests.integration.conftest import get_token


# ─────────────────────────────────────────────────────────────────────────────
# CU-TI-03 · Crear actividad — total_etapas correcto
# ─────────────────────────────────────────────────────────────────────────────
class TestCrearActividad:

    @pytest.mark.asyncio
    async def test_requiere_autenticacion(self, client: AsyncClient, seed: dict):
        """Sin token → 401."""
        resp = await client.post("/api/v1/actividades/", json={
            "titulo": "Test",
            "total_etapas": 1,
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_familia_no_puede_crear(self, client: AsyncClient, seed: dict):
        """Rol familia → 403 (solo terapeutas pueden crear actividades)."""
        email, password = seed["creds"]["familia"]
        token = await get_token(client, email, password)

        resp = await client.post(
            "/api/v1/actividades/",
            json={
                "titulo": "Actividad no permitida",
                "descripcion": "Test",
                "total_etapas": 2,
                "paciente_id": str(seed["paciente_id"]),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_crear_actividad_1_etapa(self, client: AsyncClient, seed: dict):
        """total_etapas=1 → campo persiste como 1 (no 0, no None)."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        resp = await client.post(
            "/api/v1/actividades/",
            json={
                "titulo": "Actividad 1 etapa",
                "descripcion": "Descripción de prueba",
                "objetivo": "Objetivo de prueba",
                "frecuencia": "diaria",
                "total_etapas": 1,
                "paciente_id": str(seed["paciente_id"]),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201

        data = resp.json()
        assert data["total_etapas"] == 1, (
            f"Se esperaba total_etapas=1, se obtuvo {data['total_etapas']}"
        )

    @pytest.mark.asyncio
    async def test_crear_actividad_3_etapas(self, client: AsyncClient, seed: dict):
        """total_etapas=3 → regresión del fix; antes devolvía 0 o None."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        resp = await client.post(
            "/api/v1/actividades/",
            json={
                "titulo": "Actividad con 3 etapas",
                "descripcion": "Test de regresión fix total_etapas",
                "objetivo": "Verificar que total_etapas se persiste correctamente",
                "frecuencia": "semanal",
                "total_etapas": 3,
                "paciente_id": str(seed["paciente_id"]),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201

        data = resp.json()
        assert "total_etapas" in data, "El response debe incluir el campo total_etapas"
        assert data["total_etapas"] == 3, (
            f"[REGRESIÓN] Se esperaba total_etapas=3, se obtuvo {data['total_etapas']}. "
            "El fix de total_etapas está roto."
        )

    @pytest.mark.asyncio
    async def test_crear_actividad_5_etapas(self, client: AsyncClient, seed: dict):
        """total_etapas=5 → verificación adicional con valor más alto."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        resp = await client.post(
            "/api/v1/actividades/",
            json={
                "titulo": "Actividad con 5 etapas",
                "descripcion": "Test etapas",
                "total_etapas": 5,
                "paciente_id": str(seed["paciente_id"]),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["total_etapas"] == 5

    @pytest.mark.asyncio
    async def test_actividad_en_get_por_id(self, client: AsyncClient, seed: dict):
        """La actividad creada es recuperable por su ID con el total_etapas correcto."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        # Crear actividad con 4 etapas
        create_resp = await client.post(
            "/api/v1/actividades/",
            json={
                "titulo": "Actividad para GET individual",
                "descripcion": "Verificar persistencia en GET",
                "total_etapas": 4,
                "paciente_id": str(seed["paciente_id"]),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201
        actividad_id = create_resp.json()["id"]

        # Recuperar por ID
        get_resp = await client.get(
            f"/api/v1/actividades/{actividad_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["total_etapas"] == 4


# ─────────────────────────────────────────────────────────────────────────────
# CU-TI-04 · Asignar actividad a paciente
# ─────────────────────────────────────────────────────────────────────────────
class TestAsignarActividad:

    @pytest.mark.asyncio
    async def test_actividad_asignada_aparece_en_lista(self, client: AsyncClient, seed: dict):
        """
        Actividad creada con paciente_id → debe aparecer en GET /actividades/
        filtrada por el terapeuta.
        """
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        # Crear la actividad asignada al paciente del seed
        create_resp = await client.post(
            "/api/v1/actividades/",
            json={
                "titulo": "Actividad asignada a paciente",
                "descripcion": "Test de asignación",
                "total_etapas": 2,
                "paciente_id": str(seed["paciente_id"]),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201
        actividad_id = create_resp.json()["id"]
        assert create_resp.json()["paciente_id"] == str(seed["paciente_id"])

        # Verificar que aparece en el listado
        list_resp = await client.get(
            "/api/v1/actividades/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200
        ids = [a["id"] for a in list_resp.json()]
        assert actividad_id in ids, "La actividad asignada debe aparecer en el GET /actividades/"

    @pytest.mark.asyncio
    async def test_actividad_tiene_paciente_correcto(self, client: AsyncClient, seed: dict):
        """La actividad creada referencia al paciente_id correcto."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        create_resp = await client.post(
            "/api/v1/actividades/",
            json={
                "titulo": "Verificar paciente_id",
                "total_etapas": 1,
                "paciente_id": str(seed["paciente_id"]),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201

        data = create_resp.json()
        assert data["paciente_id"] == str(seed["paciente_id"]), (
            "paciente_id en response debe coincidir con el enviado en el request"
        )

    @pytest.mark.asyncio
    async def test_actividad_paciente_inexistente(self, client: AsyncClient, seed: dict):
        """paciente_id que no existe → el endpoint debe rechazarlo (400 o 404)."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        fake_paciente_id = uuid.uuid4()
        resp = await client.post(
            "/api/v1/actividades/",
            json={
                "titulo": "Actividad con paciente inexistente",
                "total_etapas": 1,
                "paciente_id": str(fake_paciente_id),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        # Debe fallar — paciente no existe
        assert resp.status_code in (400, 404, 422), (
            f"Se esperaba un error al asignar a paciente inexistente, se obtuvo {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_desactivar_actividad(self, client: AsyncClient, seed: dict):
        """PATCH con activa=False → la actividad ya no aparece en el listado."""
        email, password = seed["creds"]["ter-int"]
        token = await get_token(client, email, password)

        # Crear
        create_resp = await client.post(
            "/api/v1/actividades/",
            json={
                "titulo": "Actividad para desactivar",
                "total_etapas": 1,
                "paciente_id": str(seed["paciente_id"]),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201
        actividad_id = create_resp.json()["id"]

        # Desactivar
        patch_resp = await client.patch(
            f"/api/v1/actividades/{actividad_id}",
            json={"activa": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert patch_resp.status_code == 200

        # Verificar que no aparece en el listado (activa=True por defecto en el GET)
        list_resp = await client.get(
            "/api/v1/actividades/",
            headers={"Authorization": f"Bearer {token}"},
        )
        ids_activos = [a["id"] for a in list_resp.json()]
        assert actividad_id not in ids_activos, (
            "Una actividad desactivada no debe aparecer en el listado de activas"
        )
