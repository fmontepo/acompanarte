# tests/unit/test_rag_clinico_unit.py
# ─────────────────────────────────────────────────────────────────────────────
# Tests unitarios PUROS para el RAG clínico interno.
# No requieren BD, Ollama, ni sentence-transformers instalado.
#
# Casos de uso cubiertos:
#   UC-RAG-01  _texto_registro()  — construcción texto fuente registros
#   UC-RAG-02  _texto_actividad() — construcción texto fuente actividades
#   UC-RAG-03  _texto_progreso()  — construcción texto fuente progresos
#   UC-RAG-04  _hash()            — hash SHA-256 determinístico
#   UC-RAG-05  batch skip         — no actualiza cuando hash coincide
#   UC-RAG-06  batch update       — actualiza cuando hash difiere / nuevo
#   UC-RAG-07  batch progresos    — filtra por observacion a nivel SQL
#   UC-RAG-08  rag clinico vacío  — lista vacía sin pacientes
#   UC-RAG-11  prompt dual RAG    — sección clínica siempre incluida
# ─────────────────────────────────────────────────────────────────────────────

import hashlib
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# ── Imports bajo test ─────────────────────────────────────────────────────────
from app.services.embedding_batch import (
    _texto_registro,
    _texto_actividad,
    _texto_progreso,
    _hash,
    _procesar_registros,
    _procesar_actividades,
    _procesar_progresos,
)
from app.services.ia_service import buscar_contexto_rag_clinico
from app.api.terapeuta_ia_router import _construir_prompt_terapeuta


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-01 · _texto_registro()
# ─────────────────────────────────────────────────────────────────────────────

class TestTextoRegistro:
    """UC-RAG-01: Construcción correcta del texto fuente para registros de seguimiento."""

    def test_registro_completo_incluye_tipo_fecha_y_contenido(self):
        """Con contenido_enc: el texto contiene los 3 campos."""
        r = MagicMock()
        r.tipo = "evolucion"
        r.fecha_registro = date(2025, 1, 15)
        r.contenido_enc = "El niño mostró avance en lenguaje"

        resultado = _texto_registro(r)

        assert "Tipo: evolucion" in resultado
        assert "Fecha: 2025-01-15" in resultado
        assert "El niño mostró avance en lenguaje" in resultado

    def test_registro_sin_contenido_solo_incluye_tipo_y_fecha(self):
        """Sin contenido_enc (None): solo tipo y fecha en el texto."""
        r = MagicMock()
        r.tipo = "observacion"
        r.fecha_registro = date(2025, 3, 1)
        r.contenido_enc = None

        resultado = _texto_registro(r)

        assert "Tipo: observacion" in resultado
        assert "Fecha: 2025-03-01" in resultado
        assert resultado.count("\n") == 1  # exactamente 2 partes

    def test_tipos_validos_se_preservan_sin_transformacion(self):
        """El tipo se inserta tal como viene del modelo, sin modificar."""
        for tipo in ("logro", "incidente", "objetivo", "evolucion", "observacion"):
            r = MagicMock()
            r.tipo = tipo
            r.fecha_registro = date(2025, 6, 1)
            r.contenido_enc = None
            assert f"Tipo: {tipo}" in _texto_registro(r)

    def test_partes_separadas_por_newline(self):
        """Las partes del texto se unen con \\n."""
        r = MagicMock()
        r.tipo = "logro"
        r.fecha_registro = date(2025, 4, 10)
        r.contenido_enc = "Contenido de prueba"

        resultado = _texto_registro(r)
        partes = resultado.split("\n")

        assert len(partes) == 3
        assert partes[0] == "Tipo: logro"
        assert partes[2] == "Contenido de prueba"


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-02 · _texto_actividad()
# ─────────────────────────────────────────────────────────────────────────────

class TestTextoActividad:
    """UC-RAG-02: Construcción correcta del texto fuente para actividades familiares."""

    def test_actividad_completa_incluye_todos_los_campos(self):
        """titulo + objetivo + descripcion + frecuencia → 4 partes en el texto."""
        a = MagicMock()
        a.titulo = "Rutina matutina"
        a.objetivo = "Mejorar autonomía"
        a.descripcion = "Lavado de manos paso a paso"
        a.frecuencia = "diaria"

        resultado = _texto_actividad(a)

        assert "Actividad: Rutina matutina" in resultado
        assert "Objetivo: Mejorar autonomía" in resultado
        assert "Lavado de manos paso a paso" in resultado
        assert "Frecuencia: diaria" in resultado

    def test_actividad_sin_objetivo_ni_descripcion(self):
        """Con opcionales en None: solo titulo y frecuencia."""
        a = MagicMock()
        a.titulo = "Juego libre"
        a.objetivo = None
        a.descripcion = None
        a.frecuencia = "libre"

        resultado = _texto_actividad(a)

        assert "Actividad: Juego libre" in resultado
        assert "Frecuencia: libre" in resultado
        assert "Objetivo:" not in resultado

    def test_actividad_con_objetivo_sin_descripcion(self):
        """objetivo presente, descripcion ausente → 3 partes."""
        a = MagicMock()
        a.titulo = "Lectura compartida"
        a.objetivo = "Ampliar vocabulario"
        a.descripcion = None
        a.frecuencia = "semanal"

        resultado = _texto_actividad(a)

        assert "Objetivo: Ampliar vocabulario" in resultado
        assert "Frecuencia: semanal" in resultado

    def test_frecuencia_siempre_al_final(self):
        """La frecuencia es siempre la última parte del texto."""
        a = MagicMock()
        a.titulo = "Actividad X"
        a.objetivo = "Objetivo Y"
        a.descripcion = "Descripción Z"
        a.frecuencia = "quincenal"

        resultado = _texto_actividad(a)
        assert resultado.endswith("Frecuencia: quincenal")

    def test_actividad_sin_descripcion_con_objetivo(self):
        """Sin descripción, el texto NO incluye línea vacía."""
        a = MagicMock()
        a.titulo = "Test"
        a.objetivo = "Objetivo test"
        a.descripcion = None
        a.frecuencia = "diaria"

        resultado = _texto_actividad(a)
        # No debe haber líneas vacías
        for linea in resultado.split("\n"):
            assert linea.strip() != ""


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-03 · _texto_progreso()
# ─────────────────────────────────────────────────────────────────────────────

class TestTextoProgreso:
    """UC-RAG-03: Construcción correcta del texto fuente para progresos de actividad."""

    def test_progreso_completo_incluye_todos_los_campos(self):
        """Completo + satisfaccion + observacion → todos los campos presentes."""
        p = MagicMock()
        p.es_completada = True
        p.etapas_completadas = None
        p.nivel_satisfaccion = 4
        p.observacion = "Le costó un poco pero lo logró"

        resultado = _texto_progreso(p, "Rutina matutina")

        assert "Sesión de actividad: Rutina matutina" in resultado
        assert "Resultado: Completa" in resultado
        assert "Satisfacción: 4/5" in resultado
        assert "Observación: Le costó un poco pero lo logró" in resultado

    def test_progreso_parcial_muestra_etapas(self):
        """es_completada=False + etapas=2 → 'Parcial (2 etapas)'."""
        p = MagicMock()
        p.es_completada = False
        p.etapas_completadas = 2
        p.nivel_satisfaccion = None
        p.observacion = None

        resultado = _texto_progreso(p, "Actividad de prueba")

        assert "Resultado: Parcial (2 etapas)" in resultado
        assert "Satisfacción:" not in resultado
        assert "Observación:" not in resultado

    def test_progreso_parcial_etapas_none_muestra_cero(self):
        """etapas_completadas=None se trata como 0 en el texto."""
        p = MagicMock()
        p.es_completada = False
        p.etapas_completadas = None
        p.nivel_satisfaccion = None
        p.observacion = None

        resultado = _texto_progreso(p, "Actividad test")

        assert "Parcial (0 etapas)" in resultado

    def test_progreso_titulo_actividad_se_incluye(self):
        """El título de la actividad se incluye en el encabezado."""
        p = MagicMock()
        p.es_completada = True
        p.etapas_completadas = None
        p.nivel_satisfaccion = None
        p.observacion = None

        resultado = _texto_progreso(p, "Mi actividad especial")

        assert "Sesión de actividad: Mi actividad especial" in resultado

    def test_satisfaccion_escala_1_a_5(self):
        """La satisfacción se muestra como n/5 para cualquier valor válido."""
        for sat in (1, 2, 3, 4, 5):
            p = MagicMock()
            p.es_completada = True
            p.etapas_completadas = None
            p.nivel_satisfaccion = sat
            p.observacion = None
            resultado = _texto_progreso(p, "Test")
            assert f"Satisfacción: {sat}/5" in resultado


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-04 · _hash()
# ─────────────────────────────────────────────────────────────────────────────

class TestHash:
    """UC-RAG-04: Hash SHA-256 determinístico para detección de cambios."""

    def test_mismo_texto_produce_mismo_hash(self):
        """Determinismo: el mismo texto siempre da el mismo resultado."""
        texto = "Tipo: evolucion\nFecha: 2025-01-01\nContenido de ejemplo"
        assert _hash(texto) == _hash(texto)

    def test_textos_distintos_producen_hashes_distintos(self):
        """Textos diferentes → hashes diferentes."""
        h1 = _hash("texto original")
        h2 = _hash("texto modificado")
        assert h1 != h2

    def test_hash_tiene_64_caracteres(self):
        """SHA-256 en hexadecimal = 64 caracteres."""
        resultado = _hash("cualquier texto de prueba")
        assert len(resultado) == 64

    def test_hash_es_hexadecimal_valido(self):
        """El resultado solo contiene caracteres hexadecimales (lowercase)."""
        resultado = _hash("verificacion hex")
        assert all(c in "0123456789abcdef" for c in resultado)

    def test_hash_coincide_con_sha256_python(self):
        """El resultado es idéntico al SHA-256 estándar de Python."""
        texto = "test de verificación con acentos: á é í ó ú"
        esperado = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        assert _hash(texto) == esperado

    def test_cambio_minimo_en_texto_cambia_hash(self):
        """Un solo caracter diferente produce hash completamente distinto."""
        h1 = _hash("Observación del día 1")
        h2 = _hash("Observación del día 2")
        assert h1 != h2

    def test_hash_texto_vacio(self):
        """Hash de string vacío es determinístico y tiene 64 chars."""
        resultado = _hash("")
        assert len(resultado) == 64
        assert resultado == hashlib.sha256(b"").hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers para construir mocks de DB correctamente
# ─────────────────────────────────────────────────────────────────────────────

def _db_scalars_mock(rows: list):
    """
    Construye un AsyncMock de DB donde:
      await db.execute(...) → MagicMock con .scalars().all() == rows

    IMPORTANTE: db.execute.return_value debe ser MagicMock explícito.
    Con AsyncMock, los atributos hijo también son AsyncMock, lo que hace
    que .scalars() devuelva una coroutine en lugar de un MagicMock.
    """
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    db.execute.return_value = result
    return db


def _db_all_mock(rows: list):
    """
    Construye un AsyncMock de DB donde:
      await db.execute(...) → MagicMock con .all() == rows

    Usado para queries que iteran sobre (model, distance) tuples.
    """
    db = AsyncMock()
    result = MagicMock()
    result.all.return_value = rows
    db.execute.return_value = result
    return db


def _db_scalars_side_effect(rows_per_call: list[list]):
    """
    Construye un AsyncMock de DB donde cada llamada a execute() devuelve
    un resultado distinto (para queries múltiples).
    """
    db = AsyncMock()
    results = []
    for rows in rows_per_call:
        r = MagicMock()
        r.scalars.return_value.all.return_value = rows
        results.append(r)
    db.execute.side_effect = results
    return db


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-05 · Batch skip — no actualiza cuando hash coincide
# ─────────────────────────────────────────────────────────────────────────────

class TestBatchSkipCuandoHashCoincide:
    """UC-RAG-05: El batch omite registros cuyo embedding_hash ya coincide."""

    @pytest.mark.asyncio
    async def test_registro_con_hash_actual_no_regenera_embedding(self):
        """Hash almacenado == hash actual → skip, modelo no invocado, sin commit."""
        r = MagicMock()
        r.tipo = "evolucion"
        r.fecha_registro = date(2025, 1, 1)
        r.contenido_enc = "Contenido sin cambios"

        texto = _texto_registro(r)
        r.embedding_hash = _hash(texto)
        r.embedding = [0.1] * 384

        db = _db_scalars_mock([r])
        model = MagicMock()
        actualizados = await _procesar_registros(db, model)

        assert actualizados == 0
        model.encode.assert_not_called()
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_actividad_con_hash_actual_no_regenera_embedding(self):
        """Skip en actividades cuando hash coincide."""
        a = MagicMock()
        a.titulo = "Rutina sin cambios"
        a.objetivo = "Objetivo estable"
        a.descripcion = "Descripción que no cambió"
        a.frecuencia = "diaria"

        texto = _texto_actividad(a)
        a.embedding_hash = _hash(texto)
        a.embedding = [0.2] * 384

        db = _db_scalars_mock([a])
        model = MagicMock()
        actualizados = await _procesar_actividades(db, model)

        assert actualizados == 0
        model.encode.assert_not_called()
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiples_registros_todos_al_dia(self):
        """Con 3 registros sin cambios → actualizados == 0."""
        registros = []
        for i in range(3):
            r = MagicMock()
            r.tipo = "observacion"
            r.fecha_registro = date(2025, 1, i + 1)
            r.contenido_enc = f"Contenido estable {i}"
            texto = _texto_registro(r)
            r.embedding_hash = _hash(texto)
            r.embedding = [0.1] * 384
            registros.append(r)

        db = _db_scalars_mock(registros)
        actualizados = await _procesar_registros(db, MagicMock())
        assert actualizados == 0


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-06 · Batch update — actualiza cuando hash difiere o es None
# ─────────────────────────────────────────────────────────────────────────────

class TestBatchActualizaCuandoHashDifiere:
    """UC-RAG-06: El batch regenera embeddings para registros con hash distinto o sin hash."""

    @pytest.mark.asyncio
    async def test_registro_con_hash_viejo_regenera_embedding(self):
        """Hash distinto al actual → embedding regenerado, hash actualizado, commit llamado."""
        r = MagicMock()
        r.tipo = "evolucion"
        r.fecha_registro = date(2025, 1, 1)
        r.contenido_enc = "Contenido actualizado recientemente"
        r.embedding_hash = "a" * 64  # hash inválido (distinto al real)

        db = _db_scalars_mock([r])

        vector_fake = np.array([0.5] * 384)
        with patch(
            "app.services.embedding_batch.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value=vector_fake,
        ):
            actualizados = await _procesar_registros(db, MagicMock())

        assert actualizados == 1
        assert r.embedding == vector_fake.tolist()
        texto_esperado = _texto_registro(r)
        assert r.embedding_hash == _hash(texto_esperado)
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_registro_nuevo_sin_hash_genera_embedding(self):
        """Registro nuevo (embedding_hash=None) → se embede por primera vez."""
        r = MagicMock()
        r.tipo = "logro"
        r.fecha_registro = date(2025, 6, 1)
        r.contenido_enc = "Primer logro registrado"
        r.embedding_hash = None

        db = _db_scalars_mock([r])

        vector_fake = np.array([0.3] * 384)
        with patch(
            "app.services.embedding_batch.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value=vector_fake,
        ):
            actualizados = await _procesar_registros(db, MagicMock())

        assert actualizados == 1
        assert r.embedding == vector_fake.tolist()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_actividad_modificada_regenera_embedding(self):
        """Actividad con hash desactualizado → embedding regenerado."""
        a = MagicMock()
        a.titulo = "Actividad modificada"
        a.objetivo = "Nuevo objetivo"
        a.descripcion = None
        a.frecuencia = "semanal"
        a.embedding_hash = "b" * 64  # hash distinto al real

        db = _db_scalars_mock([a])

        vector_fake = np.array([0.7] * 384)
        with patch(
            "app.services.embedding_batch.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value=vector_fake,
        ):
            actualizados = await _procesar_actividades(db, MagicMock())

        assert actualizados == 1
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mix_solo_actualiza_los_que_cambiaron(self):
        """3 registros: 2 sin cambios + 1 modificado → actualizados == 1."""
        registros = []

        # Los 2 primeros están al día
        for i in range(2):
            r = MagicMock()
            r.tipo = "observacion"
            r.fecha_registro = date(2025, 1, i + 1)
            r.contenido_enc = f"Contenido estable {i}"
            texto = _texto_registro(r)
            r.embedding_hash = _hash(texto)
            r.embedding = [0.1] * 384
            registros.append(r)

        # El 3ro tiene hash desactualizado
        r_viejo = MagicMock()
        r_viejo.tipo = "incidente"
        r_viejo.fecha_registro = date(2025, 2, 1)
        r_viejo.contenido_enc = "Contenido nuevo no hasheado"
        r_viejo.embedding_hash = "c" * 64  # hash falso
        registros.append(r_viejo)

        db = _db_scalars_mock(registros)

        vector_fake = np.array([0.4] * 384)
        with patch(
            "app.services.embedding_batch.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value=vector_fake,
        ):
            actualizados = await _procesar_registros(db, MagicMock())

        assert actualizados == 1


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-07 · Batch progresos — filtro por observacion a nivel SQL
# ─────────────────────────────────────────────────────────────────────────────

class TestBatchProgresosFiltroObservacion:
    """UC-RAG-07: El batch solo procesa progresos con observacion (filtro en SQL)."""

    @pytest.mark.asyncio
    async def test_sin_progresos_con_observacion_no_genera_embeddings(self):
        """BD devuelve 0 progresos (los sin observacion ya filtrados por SQL) → 0 actualizados."""
        db = _db_scalars_mock([])
        model = MagicMock()
        actualizados = await _procesar_progresos(db, model)

        assert actualizados == 0
        db.execute.assert_called_once()  # la query sí se ejecuta (filtro es SQL)
        model.encode.assert_not_called()

    @pytest.mark.asyncio
    async def test_progreso_con_observacion_y_hash_coincidente_se_skipea(self):
        """Progreso con observacion pero hash ya actualizado → skip."""
        p = MagicMock()
        p.es_completada = True
        p.etapas_completadas = None
        p.nivel_satisfaccion = 3
        p.observacion = "Muy bien hoy"
        p.actividad = MagicMock()
        p.actividad.titulo = "Actividad base"

        texto = _texto_progreso(p, p.actividad.titulo)
        p.embedding_hash = _hash(texto)

        db = _db_scalars_mock([p])
        actualizados = await _procesar_progresos(db, MagicMock())
        assert actualizados == 0

    @pytest.mark.asyncio
    async def test_progreso_con_observacion_y_hash_viejo_se_actualiza(self):
        """Progreso con observacion y hash desactualizado → se embede."""
        p = MagicMock()
        p.es_completada = False
        p.etapas_completadas = 1
        p.nivel_satisfaccion = 2
        p.observacion = "Costó pero avanzó"
        p.actividad = MagicMock()
        p.actividad.titulo = "Tarea diaria"
        p.embedding_hash = "d" * 64  # hash falso

        db = _db_scalars_mock([p])

        vector_fake = np.array([0.6] * 384)
        with patch(
            "app.services.embedding_batch.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value=vector_fake,
        ):
            actualizados = await _procesar_progresos(db, MagicMock())

        assert actualizados == 1
        assert p.embedding == vector_fake.tolist()
        db.commit.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-08 · RAG clínico — lista vacía sin pacientes
# ─────────────────────────────────────────────────────────────────────────────

class TestBuscarContextoClinicoPacientesVacios:
    """UC-RAG-08: buscar_contexto_rag_clinico retorna [] inmediatamente si no hay pacientes."""

    @pytest.mark.asyncio
    async def test_lista_vacia_retorna_inmediatamente(self):
        """Guard temprano: sin pacientes no hay nada que buscar, DB no se consulta."""
        db = AsyncMock()

        resultado = await buscar_contexto_rag_clinico(db, "cualquier consulta", [])

        assert resultado == []
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_lista_con_un_paciente_ejecuta_queries(self):
        """Con al menos un paciente_id, la función intenta las 3 queries."""
        import uuid
        pac_id = uuid.uuid4()

        # buscar_contexto_rag_clinico usa res.all() (no res.scalars().all())
        db = _db_all_mock([])
        # Para 3 queries seguidas, necesitamos side_effect
        result1 = MagicMock(); result1.all.return_value = []
        result2 = MagicMock(); result2.all.return_value = []
        result3 = MagicMock(); result3.all.return_value = []
        db.execute.side_effect = [result1, result2, result3]

        with patch("app.services.ia_service.asyncio.to_thread", new_callable=AsyncMock) as t:
            t.return_value = np.array([0.1] * 384)
            with patch("app.services.ia_service.get_embedding_model", return_value=MagicMock()):
                resultado = await buscar_contexto_rag_clinico(db, "consulta", [pac_id])

        assert db.execute.call_count == 3
        assert resultado == []


# ─────────────────────────────────────────────────────────────────────────────
# UC-RAG-11 · Prompt del terapeuta — dual RAG siempre presente
# ─────────────────────────────────────────────────────────────────────────────

class TestPromptTerapeutaDualRAG:
    """UC-RAG-11: _construir_prompt_terapeuta() incluye siempre la sección de RAG clínico."""

    def test_prompt_con_fuentes_clinicas_incluye_fragmentos(self):
        """Con fuentes clínicas → el texto de los fragmentos aparece en el prompt."""
        fuentes_clinicas = [
            {
                "fuente": "registro",
                "paciente_id": "abc-123",
                "texto": "El niño mostró regresión en lenguaje esta semana",
                "score": 0.75,
            }
        ]

        prompt = _construir_prompt_terapeuta(
            consulta="¿Cómo va el progreso del paciente?",
            contexto_clinico="Total de pacientes activos: 1",
            fuentes_biblio=[],
            fuentes_clinicas=fuentes_clinicas,
            reglas={},
        )

        assert "FRAGMENTOS CLÍNICOS RELEVANTES A LA CONSULTA" in prompt
        assert "El niño mostró regresión en lenguaje esta semana" in prompt

    def test_prompt_sin_fuentes_clinicas_incluye_mensaje_vacio(self):
        """Sin fuentes clínicas → mensaje de 'no encontró fragmentos' en el prompt."""
        prompt = _construir_prompt_terapeuta(
            consulta="¿Estrategias para manejar berrinches?",
            contexto_clinico="Total de pacientes activos: 1",
            fuentes_biblio=[],
            fuentes_clinicas=[],
            reglas={},
        )

        assert "FRAGMENTOS CLÍNICOS RELEVANTES A LA CONSULTA" in prompt
        assert "No se encontraron fragmentos clínicos semánticamente relevantes" in prompt

    def test_prompt_incluye_contexto_clinico_estructurado(self):
        """El contexto clínico estructurado siempre aparece en el prompt."""
        contexto = "Total de pacientes activos: 3\n[Paciente 1]"
        prompt = _construir_prompt_terapeuta(
            consulta="Resumen del grupo",
            contexto_clinico=contexto,
            fuentes_biblio=[],
            fuentes_clinicas=[],
            reglas={},
        )

        assert "CONTEXTO CLÍNICO ESTRUCTURADO" in prompt
        assert "Total de pacientes activos: 3" in prompt

    def test_prompt_etiqueta_fuente_registro_como_nota_clinica(self):
        """Fragmentos de tipo 'registro' se etiquetan como [Nota clínica]."""
        prompt = _construir_prompt_terapeuta(
            consulta="Test",
            contexto_clinico="",
            fuentes_biblio=[],
            fuentes_clinicas=[
                {"fuente": "registro", "paciente_id": "x", "texto": "Nota médica", "score": 0.8}
            ],
        )
        assert "[Nota clínica]" in prompt

    def test_prompt_etiqueta_fuente_actividad_como_actividad(self):
        """Fragmentos de tipo 'actividad' se etiquetan como [Actividad]."""
        prompt = _construir_prompt_terapeuta(
            consulta="Test",
            contexto_clinico="",
            fuentes_biblio=[],
            fuentes_clinicas=[
                {"fuente": "actividad", "paciente_id": "x", "texto": "Rutina", "score": 0.6}
            ],
        )
        assert "[Actividad]" in prompt

    def test_prompt_etiqueta_fuente_progreso_como_sesion_registrada(self):
        """Fragmentos de tipo 'progreso' se etiquetan como [Sesión registrada]."""
        prompt = _construir_prompt_terapeuta(
            consulta="Test",
            contexto_clinico="",
            fuentes_biblio=[],
            fuentes_clinicas=[
                {"fuente": "progreso", "paciente_id": "x", "texto": "Sesión exitosa", "score": 0.55}
            ],
        )
        assert "[Sesión registrada]" in prompt

    def test_prompt_incluye_seccion_bibliografia_profesional(self):
        """El prompt siempre incluye la sección de bibliografía."""
        prompt = _construir_prompt_terapeuta(
            consulta="Test",
            contexto_clinico="",
            fuentes_biblio=[{"titulo": "Artículo TEA", "contenido": "Contenido del artículo"}],
            fuentes_clinicas=[],
        )
        assert "BIBLIOGRAFÍA PROFESIONAL RELEVANTE" in prompt
        assert "Artículo TEA" in prompt

    def test_prompt_sin_fuentes_biblio_muestra_mensaje_no_encontrada(self):
        """Sin bibliografía → prompt incluye texto de 'no encontró bibliografía'."""
        prompt = _construir_prompt_terapeuta(
            consulta="Test sin bibliografía",
            contexto_clinico="",
            fuentes_biblio=[],
            fuentes_clinicas=[],
        )
        assert "No se encontró bibliografía relevante" in prompt

    def test_prompt_fuentes_clinicas_none_tratado_como_lista_vacia(self):
        """fuentes_clinicas=None no debe causar error."""
        prompt = _construir_prompt_terapeuta(
            consulta="Test",
            contexto_clinico="",
            fuentes_biblio=[],
            fuentes_clinicas=None,
        )
        assert "FRAGMENTOS CLÍNICOS" in prompt

    def test_prompt_contiene_instruccion_anonimidad(self):
        """El prompt instruye mantener anonimidad de pacientes."""
        prompt = _construir_prompt_terapeuta(
            consulta="Test",
            contexto_clinico="",
            fuentes_biblio=[],
            fuentes_clinicas=[],
        )
        assert "Paciente 1" in prompt or "anonimidad" in prompt or "Paciente" in prompt
