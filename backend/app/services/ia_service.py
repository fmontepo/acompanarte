# app/services/ia_service.py
# Servicio de IA — pipeline RAG completo
# Arquitectura: Ollama corre en Windows, el backend en Docker
# La comunicación es via HTTP a host.docker.internal:11434
#
# RESTRICCIONES (no negociables):
#   1. Anonimizar PII antes de cualquier procesamiento
#   2. Buscar contexto SOLO en recursos validados (pgvector)
#   3. Aplicar filtro anti-diagnóstico a toda respuesta
#   4. Registrar cada interacción en auditoría
#   5. Generar alerta si el mensaje contiene señales sensibles

import re
import os
import httpx
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sentence_transformers import SentenceTransformer

from app.models.recursoProfesional import RecursoProfesional
from app.models.ia import SesionIA, MensajeIA
from app.models.alerta import Alerta
from app.models.regla_ia import ReglaIA

# ---------------------------------------------------------------------------
# Configuración — desde variables de entorno
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

MAX_CONTEXT_CHUNKS = 4
SIMILARITY_THRESHOLD = 0.35   # calibrado para paraphrase-multilingual-MiniLM-L12-v2

# Número máximo de reglas por tipo que se inyectan en el prompt
# (evita que el bloque de reglas supere el num_ctx del modelo)
MAX_REGLAS_POR_TIPO = 10

# Palabras/frases que activan el filtro anti-diagnóstico
PATRONES_DIAGNOSTICO = [
    r"\btu hijo tiene\b",
    r"\bpadece de\b",
    r"\bdiagnóstico de\b",
    r"\bes autista\b",
    r"\btiene TEA\b",
    r"\btiene autismo\b",
    r"\bsufre de\b",
]

# Señales de alerta que requieren escalamiento humano.
# CRITERIO: solo situaciones de riesgo real, no consultas clínicas generales.
# "crisis" solo se usa en frases que indican urgencia, no como término técnico.
PATRONES_ALERTA = [
    r"\bse lastima\b",
    r"\bse hace daño\b",
    r"\bse golpea\b",
    r"\bse muerde\b",
    r"\bse araña\b",
    r"\bautolesion\b",
    r"\bse pega\b",
    r"\bno come nada\b",         # más específico que "no come"
    r"\bdías sin comer\b",
    r"\bno duerme nada\b",       # más específico que "no duerme"
    r"\bnoches sin dormir\b",
    r"\bcrisis\s+frecuente",     # "crisis frecuentes" / "crisis seguidas"
    r"\bmucha[s]?\s+crisis\b",
    r"\bcrisis\s+cada\b",        # "crisis cada día" / "crisis cada hora"
    r"\bagresiv\w*\s+(?:much|muy|constant|siemp)",  # agresividad constante/mucha
    r"\bno\s+responde\s+(?:a\s+nada|para\s+nada|nunca)\b",
    r"\bregresión\s+(?:total|completa|severa|en\s+todo)\b",
    r"\bno\s+habla\s+(?:más|nada|nunca)\b",         # perdió el habla
]

# Singleton del modelo de embeddings
_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


# ---------------------------------------------------------------------------
# Paso 1: Anonimización de PII
# ---------------------------------------------------------------------------
def anonimizar_pii(texto: str) -> str:
    texto = re.sub(r"\b\d{2}[\.\s]?\d{3}[\.\s]?\d{3}\b", "[DNI]", texto)
    texto = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", texto)
    texto = re.sub(r"\b(\+54|0)\s?\d{2,4}\s?\d{6,8}\b", "[TELEFONO]", texto)
    return texto


# ---------------------------------------------------------------------------
# Paso 1b: Carga de reglas de comportamiento activas
# ---------------------------------------------------------------------------
async def cargar_reglas(
    db: AsyncSession,
    contexto: str = "familiar",
) -> dict[str, list[str]]:
    """
    Devuelve las reglas activas agrupadas por tipo.
    { 'positiva': [...textos...], 'negativa': [...textos...] }
    Incluye reglas del contexto solicitado + las 'global' (aplican a todos).
    Ordenadas por orden ASC para respetar la prioridad definida por el admin.
    """
    result = await db.execute(
        select(ReglaIA)
        .where(
            ReglaIA.activa == True,
            ReglaIA.contexto.in_([contexto, "global"]),
        )
        .order_by(ReglaIA.tipo, ReglaIA.orden)
        .limit(MAX_REGLAS_POR_TIPO * 2)
    )
    reglas = result.scalars().all()
    agrupadas: dict[str, list[str]] = {"positiva": [], "negativa": []}
    for r in reglas:
        if r.tipo in agrupadas and len(agrupadas[r.tipo]) < MAX_REGLAS_POR_TIPO:
            agrupadas[r.tipo].append(r.texto)
    return agrupadas


def _bloque_reglas(reglas: dict[str, list[str]]) -> str:
    """
    Genera el bloque de texto que se inyecta en el prompt con las reglas.
    Si no hay reglas de ningún tipo, devuelve cadena vacía.
    """
    positivas = reglas.get("positiva", [])
    negativas = reglas.get("negativa", [])
    if not positivas and not negativas:
        return ""

    lineas = ["--- REGLAS DE COMPORTAMIENTO ---"]
    if positivas:
        lineas.append("PODÉS responder sobre:")
        for t in positivas:
            lineas.append(f"  ✓ {t}")
    if negativas:
        lineas.append("NO DEBES:")
        for t in negativas:
            lineas.append(f"  ✗ {t}")
    lineas.append("--- FIN REGLAS ---")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Paso 2: Búsqueda semántica en pgvector (RAG)
# ---------------------------------------------------------------------------
async def buscar_contexto_rag(
    db: AsyncSession,
    consulta: str,
    top_k: int = MAX_CONTEXT_CHUNKS,
) -> list[dict]:
    model = get_embedding_model()
    embedding = model.encode(consulta).tolist()

    result = await db.execute(
        select(
            RecursoProfesional,
            RecursoProfesional.embedding.cosine_distance(embedding).label("distancia")
        )
        .where(RecursoProfesional.validado == True)
        .where(RecursoProfesional.activo == True)
        .where(RecursoProfesional.embedding.is_not(None))
        .order_by("distancia")
        .limit(top_k)
    )
    rows = result.all()

    fuentes = []
    for recurso, distancia in rows:
        score = 1 - distancia
        if score >= SIMILARITY_THRESHOLD:
            fuentes.append({
                "recurso_id": str(recurso.id),
                "titulo": recurso.titulo,
                "contenido": recurso.contenido_texto or recurso.descripcion or "",
                "score": round(score, 4),
            })
    return fuentes


# ---------------------------------------------------------------------------
# Paso 3: Construcción del prompt RAG
# ---------------------------------------------------------------------------
MAX_CHARS_POR_FUENTE = 800   # limitar contexto para no exceder el num_ctx del modelo


def construir_prompt(consulta: str, fuentes: list[dict], reglas: dict | None = None) -> str:
    contexto = "\n\n".join(
        f"[Fuente: {f['titulo']}]\n{f['contenido'][:MAX_CHARS_POR_FUENTE]}" for f in fuentes
    )
    bloque = _bloque_reglas(reglas or {})
    reglas_section = f"\n{bloque}\n" if bloque else ""
    return f"""Eres un asistente de apoyo para familias con niños en el espectro autista.
Tu rol es orientar y acompañar, NUNCA diagnosticar.
{reglas_section}
Basá tu respuesta EXCLUSIVAMENTE en la siguiente bibliografía validada:

--- BIBLIOGRAFÍA ---
{contexto}
--- FIN BIBLIOGRAFÍA ---

Consulta del familiar:
{consulta}

Respondé en español, con empatía y claridad. Si no encontrás información suficiente en la bibliografía, indicalo honestamente."""


# ---------------------------------------------------------------------------
# Paso 4: Llamada a Ollama via HTTP (corre en Windows)
# ---------------------------------------------------------------------------
async def generar_respuesta_ollama(prompt: str) -> str:
    """
    Llama a Ollama via API REST.
    Ollama corre en Windows, accesible desde Docker via host.docker.internal.
    Documentación: https://github.com/ollama/ollama/blob/main/docs/api.md
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 512,
            "num_ctx": 4096,      # contexto ampliado para prompts RAG con bibliografía
        }
    }

    try:
        # Timeout extendido: llama3.1:8b puede tardar 2-3 min en la primera carga
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

    except httpx.ConnectError:
        return (
            "El servicio de IA no está disponible en este momento. "
            "Por favor, verificá que Ollama esté corriendo en Windows "
            "y consultá directamente con tu terapeuta."
        )
    except httpx.TimeoutException:
        import logging
        logging.warning(f"[Ollama] Timeout después de 300s. Prompt length: {len(prompt)} chars")
        return (
            "La consulta tardó demasiado en procesarse. "
            "Intentá de nuevo en unos segundos."
        )
    except Exception as e:
        import logging
        logging.error(f"[Ollama] Error inesperado: {type(e).__name__}: {e}")
        return (
            "No pude procesar tu consulta en este momento. "
            "Por favor, contactá directamente con el terapeuta de tu equipo."
        )


# ---------------------------------------------------------------------------
# Paso 5: Filtro anti-diagnóstico
# ---------------------------------------------------------------------------
def aplicar_filtro_diagnostico(respuesta: str) -> tuple[str, bool]:
    filtro_aplicado = False
    for patron in PATRONES_DIAGNOSTICO:
        if re.search(patron, respuesta, re.IGNORECASE):
            respuesta = re.sub(
                patron,
                "[contenido omitido por política de seguridad]",
                respuesta,
                flags=re.IGNORECASE,
            )
            filtro_aplicado = True
    return respuesta, filtro_aplicado


# ---------------------------------------------------------------------------
# Paso 6: Detección de señales de alerta
# ---------------------------------------------------------------------------
def detectar_alerta(texto: str) -> tuple[bool, str]:
    for patron in PATRONES_ALERTA:
        if re.search(patron, texto, re.IGNORECASE):
            return True, "escalamiento"
    return False, ""


# ---------------------------------------------------------------------------
# Pipeline completo — punto de entrada principal
# ---------------------------------------------------------------------------
async def procesar_consulta_ia(
    db: AsyncSession,
    sesion_id: UUID,
    familiar_id: UUID,
    mensaje: str,
) -> dict:
    # 1. Anonimizar PII
    mensaje_anonimo = anonimizar_pii(mensaje)

    # 2. Detectar alerta en el mensaje del usuario
    genera_alerta, tipo_alerta = detectar_alerta(mensaje_anonimo)

    # 3. Cargar reglas activas y buscar contexto RAG en pgvector
    reglas = await cargar_reglas(db)
    fuentes = await buscar_contexto_rag(db, mensaje_anonimo)

    # 4. Generar respuesta via Ollama
    if fuentes:
        prompt = construir_prompt(mensaje_anonimo, fuentes, reglas)
        respuesta = await generar_respuesta_ollama(prompt)
    else:
        respuesta = (
            "No encontré información específica sobre tu consulta en nuestra "
            "bibliografía validada. Te recomiendo consultar directamente con "
            "el terapeuta de tu equipo."
        )

    # 5. Filtro anti-diagnóstico
    respuesta, filtro_aplicado = aplicar_filtro_diagnostico(respuesta)

    # 6. Persistir mensaje del usuario
    msg_usuario = MensajeIA(
        sesion_id=sesion_id,
        contenido=mensaje_anonimo,
        emisor="usuario",
        genera_alerta=genera_alerta,
        fuentes_rag=None,
        filtro_aplicado=False,
    )
    db.add(msg_usuario)

    # 7. Persistir respuesta IA
    fuentes_para_db = [
        {"recurso_id": f["recurso_id"], "titulo": f["titulo"], "score": f["score"]}
        for f in fuentes
    ]
    msg_ia = MensajeIA(
        sesion_id=sesion_id,
        contenido=respuesta,
        emisor="ia",
        genera_alerta=False,
        fuentes_rag=fuentes_para_db if fuentes_para_db else None,
        filtro_aplicado=filtro_aplicado,
    )
    db.add(msg_ia)

    # 8. Crear alerta si corresponde
    if genera_alerta:
        alerta = Alerta(
            sesion_id=sesion_id,
            tipo=tipo_alerta,
            severidad=2,
            descripcion=f"Señal detectada: '{mensaje_anonimo[:100]}...'",
            resuelta=False,
        )
        db.add(alerta)

    await db.commit()

    return {
        "respuesta": respuesta,
        "alerta": genera_alerta,
        "fuentes": [
            {"titulo": f["titulo"], "score": f["score"]} for f in fuentes
        ],
        "filtro_aplicado": filtro_aplicado,
    }


# ---------------------------------------------------------------------------
# Pipeline público — sin sesión ni familiar_id (chat público desde login)
# No persiste mensajes — solo genera la respuesta via RAG
# ---------------------------------------------------------------------------
async def procesar_consulta_publica(
    db: AsyncSession,
    mensaje: str,
) -> dict:
    """
    Pipeline RAG para consultas públicas anónimas.
    No requiere familiar_id ni crea registros de sesión.
    Usado por el Asistente TEA accesible desde la pantalla de login.
    """
    # 1. Anonimizar PII
    mensaje_anonimo = anonimizar_pii(mensaje)

    # 2. Detectar señales de alerta
    genera_alerta, _ = detectar_alerta(mensaje_anonimo)

    # 3. Cargar reglas activas y buscar contexto RAG en pgvector
    reglas = await cargar_reglas(db)
    fuentes = await buscar_contexto_rag(db, mensaje_anonimo)

    # 4. Generar respuesta via Ollama
    if fuentes:
        prompt = construir_prompt_publico(mensaje_anonimo, fuentes, reglas)
        respuesta = await generar_respuesta_ollama(prompt)
    else:
        respuesta = (
            "No encontré información específica sobre tu consulta en nuestra "
            "base de conocimiento. Te recomiendo consultar con un especialista "
            "en desarrollo infantil o un profesional especializado en TEA."
        )

    # 5. Filtro anti-diagnóstico
    respuesta, filtro_aplicado = aplicar_filtro_diagnostico(respuesta)

    return {
        "respuesta": respuesta,
        "alerta": genera_alerta,
        "fuentes": [{"titulo": f["titulo"], "score": f["score"]} for f in fuentes],
        "filtro_aplicado": filtro_aplicado,
    }


# ---------------------------------------------------------------------------
# Prompt especializado para consultas públicas (orientación TEA)
# ---------------------------------------------------------------------------
def construir_prompt_publico(consulta: str, fuentes: list[dict], reglas: dict | None = None) -> str:
    contexto = "\n\n".join(
        f"[Fuente: {f['titulo']}]\n{f['contenido'][:MAX_CHARS_POR_FUENTE]}" for f in fuentes
    )
    bloque = _bloque_reglas(reglas or {})
    reglas_section = f"\n{bloque}\n" if bloque else ""
    return f"""Eres un asistente de orientación para familias que tienen dudas sobre el desarrollo infantil y el espectro autista (TEA).
Tu rol es orientar, informar y acompañar. NUNCA debes diagnosticar ni reemplazar la evaluación profesional.
Si detectás señales que podrían requerir evaluación, siempre recomendá consultar con un especialista.
{reglas_section}
Basá tu respuesta EXCLUSIVAMENTE en la siguiente bibliografía validada:

--- BIBLIOGRAFÍA ---
{contexto}
--- FIN BIBLIOGRAFÍA ---

Consulta:
{consulta}

Respondé en español, con empatía y claridad. Si no encontrás información suficiente en la bibliografía, indicalo honestamente y recomendá consultar con un profesional."""
