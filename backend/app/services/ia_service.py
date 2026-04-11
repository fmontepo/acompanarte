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
SIMILARITY_THRESHOLD = 0.65

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

# Señales de alerta que requieren escalamiento humano
PATRONES_ALERTA = [
    r"\bse lastima\b", r"\bse hace daño\b", r"\bse golpea\b",
    r"\bno come\b", r"\bno duerme\b",
    r"\bcrisis\b", r"\bagresiv\b", r"\bautolesion\b",
    r"\bno responde\b", r"\bregresión\b",
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
def construir_prompt(consulta: str, fuentes: list[dict]) -> str:
    contexto = "\n\n".join(
        f"[Fuente: {f['titulo']}]\n{f['contenido']}" for f in fuentes
    )
    return f"""Eres un asistente de apoyo para familias con niños en el espectro autista.
Tu rol es orientar y acompañar, NUNCA diagnosticar.
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
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
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
    except Exception as e:
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

    # 3. Buscar contexto RAG en pgvector
    fuentes = await buscar_contexto_rag(db, mensaje_anonimo)

    # 4. Generar respuesta via Ollama
    if fuentes:
        prompt = construir_prompt(mensaje_anonimo, fuentes)
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
