# app/api/sesion_ia_router.py
# Endpoints del módulo IA — el más crítico del sistema
# Implementa el contrato de API definido en la arquitectura:
#   POST /ia/consulta → pipeline RAG completo

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.ia import SesionIA, MensajeIA
from app.schemas.sesion_ia import SesionIACreate, SesionIARead
from app.api.deps import CurrentUser, require_roles
from app.services.ia_service import procesar_consulta_ia
from app.models.contacto_publico import ContactoPublico
from app.models.regla_ia import ReglaIA

router = APIRouter(prefix="/ia", tags=["Inteligencia Artificial"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas para el endpoint simplificado /ia/chat
# ─────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    mensaje: str
    contexto: Optional[str] = None
    sesion_id: Optional[str] = None    # si ya hay una sesión activa


class ChatResponse(BaseModel):
    respuesta: str
    sesion_id: Optional[str] = None
    fuentes: list = []


class ChatPublicoResponse(BaseModel):
    respuesta: str
    fuentes: list = []
    alerta: bool = False


class ContactoPublicoRequest(BaseModel):
    nombre: str
    celular: Optional[str] = None
    mail: Optional[str] = None
    comentario: Optional[str] = None
    mensaje_alerta: str
    respuesta_ia: str


class ContactoPublicoResponse(BaseModel):
    ok: bool
    mensaje: str


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/ia/chat — endpoint simplificado para el frontend
# Maneja la gestión de sesión internamente
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat con el asistente IA (interfaz simplificada)",
)
async def chat_ia(
    body: ChatRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint simplificado para el asistente de chat.
    Gestiona la sesión IA automáticamente.
    Si el pipeline RAG no está disponible, devuelve una respuesta fallback.
    """
    if not body.mensaje or not body.mensaje.strip():
        raise HTTPException(status_code=422, detail="El mensaje no puede estar vacío")

    # Intentar llamar al pipeline RAG real
    try:
        from app.models.familiar import Familiar
        familiar_q = await db.execute(
            select(Familiar).where(Familiar.usuario_id == current_user.id)
        )
        familiar = familiar_q.scalar_one_or_none()

        if familiar:
            # Reusar sesión existente o crear nueva
            sesion_id_uuid = None
            if body.sesion_id:
                try:
                    sesion_id_uuid = UUID(body.sesion_id)
                    sesion_q = await db.execute(
                        select(SesionIA).where(SesionIA.id == sesion_id_uuid, SesionIA.estado == "activa")
                    )
                    if not sesion_q.scalar_one_or_none():
                        sesion_id_uuid = None
                except Exception:
                    sesion_id_uuid = None

            if not sesion_id_uuid:
                # Crear nueva sesión
                sesion = SesionIA(
                    id=uuid4(),
                    familiar_id=familiar.id,
                    estado="activa",
                    contexto_anonimo=body.contexto or "",
                )
                db.add(sesion)
                await db.commit()
                await db.refresh(sesion)
                sesion_id_uuid = sesion.id

            # Ejecutar RAG
            resultado = await procesar_consulta_ia(
                db=db,
                sesion_id=sesion_id_uuid,
                familiar_id=familiar.id,
                mensaje=body.mensaje.strip(),
            )
            return ChatResponse(
                respuesta=resultado.get("respuesta", "No pude procesar tu consulta."),
                sesion_id=str(sesion_id_uuid),
                fuentes=resultado.get("fuentes", []),
            )
    except Exception:
        pass  # Fallback a respuesta genérica si el RAG falla

    # Respuesta fallback cuando RAG no está disponible
    return ChatResponse(
        respuesta=(
            "El asistente de IA está disponible. Podés preguntarme sobre actividades, "
            "estrategias para el día a día, o sobre el plan terapéutico de tu familiar. "
            "En este momento estoy operando en modo básico — el módulo RAG se activará "
            "cuando esté configurado el modelo de lenguaje local."
        ),
        sesion_id=body.sesion_id,
        fuentes=[],
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/ia/chat-publico — chat sin autenticación (pantalla de login)
# Accesible por cualquier persona sin necesidad de cuenta
# No persiste sesiones — solo ejecuta el pipeline RAG
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/chat-publico",
    response_model=ChatPublicoResponse,
    summary="Chat público con el asistente TEA (sin autenticación)",
)
async def chat_ia_publico(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint público para el asistente de orientación TEA.
    No requiere autenticación. No crea sesiones en la BD.
    Disponible desde la pantalla de login para cualquier persona.
    """
    if not body.mensaje or not body.mensaje.strip():
        raise HTTPException(status_code=422, detail="El mensaje no puede estar vacío")

    try:
        from app.services.ia_service import procesar_consulta_publica
        resultado = await procesar_consulta_publica(
            db=db,
            mensaje=body.mensaje.strip(),
        )
        return ChatPublicoResponse(
            respuesta=resultado.get("respuesta", "No pude procesar tu consulta."),
            fuentes=resultado.get("fuentes", []),
            alerta=resultado.get("alerta", False),
        )
    except Exception:
        pass  # Fallback si el pipeline RAG no está disponible

    return ChatPublicoResponse(
        respuesta=(
            "El asistente de orientación TEA está disponible para ayudarte. "
            "Podés consultarme sobre señales de desarrollo infantil, estrategias "
            "de apoyo, o cómo acceder a una evaluación profesional.\n\n"
            "En este momento estoy operando en modo básico — el módulo de IA "
            "completo se activará cuando esté configurado el modelo local."
        ),
        fuentes=[],
        alerta=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/ia/contacto-publico — guardar solicitud de contacto anónima
# Cuando el usuario acepta ser contactado tras una alerta en el chat público
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/contacto-publico",
    response_model=ContactoPublicoResponse,
    summary="Guardar solicitud de contacto desde el asistente público",
)
async def contacto_publico(
    body: ContactoPublicoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra una solicitud de contacto anónima generada desde el asistente público.
    No requiere autenticación.
    Guarda nombre, comentario opcional, y el intercambio que activó la alerta.
    """
    if not body.nombre or not body.nombre.strip():
        raise HTTPException(status_code=422, detail="El nombre es obligatorio")
    if not body.mensaje_alerta or not body.respuesta_ia:
        raise HTTPException(status_code=422, detail="Faltan datos del mensaje de alerta")

    contacto = ContactoPublico(
        nombre=body.nombre.strip(),
        celular=body.celular.strip() if body.celular else None,
        mail=body.mail.strip().lower() if body.mail else None,
        comentario=body.comentario.strip() if body.comentario else None,
        mensaje_alerta=body.mensaje_alerta,
        respuesta_ia=body.respuesta_ia,
    )
    db.add(contacto)
    await db.commit()

    return ContactoPublicoResponse(
        ok=True,
        mensaje="Tu solicitud fue registrada. Un terapeuta se pondrá en contacto contigo pronto.",
    )


# ---------------------------------------------------------------------------
# POST /api/v1/ia/sesion — iniciar nueva sesión IA
# ---------------------------------------------------------------------------
@router.post(
    "/sesion",
    response_model=SesionIARead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("familiar", "terapeuta", "admin"))],
    summary="Iniciar nueva sesión de consulta IA",
)
async def iniciar_sesion(
    data: SesionIACreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Obtener el familiar asociado al usuario
    from app.models.familiar import Familiar
    result = await db.execute(
        select(Familiar).where(Familiar.usuario_id == current_user.id)
    )
    familiar = result.scalar_one_or_none()

    if not familiar:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo familiares pueden iniciar sesiones de consulta IA"
        )

    sesion = SesionIA(
        id=uuid4(),
        familiar_id=familiar.id,
        paciente_id=data.paciente_id,
        estado="activa",
        contexto_anonimo=data.contexto_anonimo,
    )
    db.add(sesion)
    await db.commit()
    await db.refresh(sesion)
    return sesion


# ---------------------------------------------------------------------------
# POST /api/v1/ia/consulta — enviar consulta al asistente IA (pipeline RAG)
# ---------------------------------------------------------------------------
@router.post(
    "/consulta",
    summary="Enviar consulta al asistente IA",
)
async def consulta_ia(
    sesion_id: UUID,
    mensaje: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Verificar que la sesión existe y pertenece al usuario
    result = await db.execute(
        select(SesionIA).where(SesionIA.id == sesion_id)
    )
    sesion = result.scalar_one_or_none()

    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada"
        )

    if sesion.estado != "activa":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La sesión no está activa"
        )

    if not mensaje or not mensaje.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El mensaje no puede estar vacío"
        )

    # Ejecutar pipeline RAG completo
    resultado = await procesar_consulta_ia(
        db=db,
        sesion_id=sesion_id,
        familiar_id=sesion.familiar_id,
        mensaje=mensaje.strip(),
    )

    return resultado


# ---------------------------------------------------------------------------
# POST /api/v1/ia/sesion/{id}/cerrar — cerrar sesión
# ---------------------------------------------------------------------------
@router.post(
    "/sesion/{sesion_id}/cerrar",
    response_model=SesionIARead,
    summary="Cerrar sesión de consulta IA",
)
async def cerrar_sesion(
    sesion_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SesionIA).where(SesionIA.id == sesion_id)
    )
    sesion = result.scalar_one_or_none()

    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada"
        )

    sesion.estado = "cerrada"
    sesion.cerrada_en = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sesion)
    return sesion


# ---------------------------------------------------------------------------
# GET /api/v1/ia/sesion/{id}/mensajes — historial de mensajes
# ---------------------------------------------------------------------------
@router.get(
    "/sesion/{sesion_id}/mensajes",
    summary="Obtener historial de mensajes de una sesión",
)
async def historial_mensajes(
    sesion_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MensajeIA)
        .where(MensajeIA.sesion_id == sesion_id)
        .order_by(MensajeIA.enviado_en.asc())
    )
    return result.scalars().all()


# =============================================================================
# ADMIN — Reglas de comportamiento del Asistente IA
# Definidas aquí (en lugar de regla_ia_router.py) para garantizar que
# uvicorn --reload las detecte al modificar este archivo existente.
# Paths: /api/v1/admin/reglas-ia  (mismo contrato que el frontend espera)
# =============================================================================

reglas_router = APIRouter(
    prefix="/admin/reglas-ia",
    tags=["Admin — Reglas IA"],
    dependencies=[Depends(require_roles("admin"))],
)


class _ReglaCreate(BaseModel):
    tipo: str
    texto: str
    descripcion: Optional[str] = None
    activa: bool = True
    orden: int = 0


class _ReglaUpdate(BaseModel):
    texto: Optional[str] = None
    descripcion: Optional[str] = None
    activa: Optional[bool] = None
    orden: Optional[int] = None


def _regla_dict(r: ReglaIA) -> dict:
    return {
        "id":             str(r.id),
        "tipo":           r.tipo,
        "texto":          r.texto,
        "descripcion":    r.descripcion,
        "activa":         r.activa,
        "orden":          r.orden,
        "creado_en":      r.creado_en,
        "actualizado_en": r.actualizado_en,
    }


@reglas_router.get("", summary="Listar reglas de IA (admin)")
async def listar_reglas_ia(
    tipo: Optional[str] = None,
    solo_activas: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(ReglaIA).order_by(ReglaIA.tipo, ReglaIA.orden, ReglaIA.creado_en)
    if tipo in ("positiva", "negativa"):
        q = q.where(ReglaIA.tipo == tipo)
    if solo_activas:
        q = q.where(ReglaIA.activa == True)
    result = await db.execute(q)
    return [_regla_dict(r) for r in result.scalars().all()]


@reglas_router.post("", summary="Crear regla de IA (admin)", status_code=201)
async def crear_regla_ia(
    body: _ReglaCreate,
    db: AsyncSession = Depends(get_db),
):
    if body.tipo not in ("positiva", "negativa"):
        raise HTTPException(400, detail="tipo debe ser 'positiva' o 'negativa'")
    if not body.texto.strip():
        raise HTTPException(400, detail="El texto de la regla no puede estar vacío")
    regla = ReglaIA(
        tipo=body.tipo,
        texto=body.texto.strip(),
        descripcion=body.descripcion.strip() if body.descripcion else None,
        activa=body.activa,
        orden=body.orden,
    )
    db.add(regla)
    await db.commit()
    await db.refresh(regla)
    return _regla_dict(regla)


@reglas_router.patch("/{regla_id}", summary="Editar regla de IA (admin)")
async def editar_regla_ia(
    regla_id: UUID,
    body: _ReglaUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ReglaIA).where(ReglaIA.id == regla_id))
    regla = result.scalar_one_or_none()
    if not regla:
        raise HTTPException(404, detail="Regla no encontrada")
    if body.texto is not None:
        if not body.texto.strip():
            raise HTTPException(400, detail="El texto no puede estar vacío")
        regla.texto = body.texto.strip()
    if body.descripcion is not None:
        regla.descripcion = body.descripcion.strip() or None
    if body.activa is not None:
        regla.activa = body.activa
    if body.orden is not None:
        regla.orden = body.orden
    await db.commit()
    await db.refresh(regla)
    return _regla_dict(regla)


@reglas_router.delete("/{regla_id}", summary="Eliminar regla de IA (admin)", status_code=204)
async def eliminar_regla_ia(
    regla_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ReglaIA).where(ReglaIA.id == regla_id))
    regla = result.scalar_one_or_none()
    if not regla:
        raise HTTPException(404, detail="Regla no encontrada")
    await db.delete(regla)
    await db.commit()
