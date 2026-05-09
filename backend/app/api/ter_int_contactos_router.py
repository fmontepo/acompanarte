# app/api/ter_int_contactos_router.py
# Contactos TEA derivados — vista del terapeuta interno
# Solo accesible para terapeutas internos (rol "ter-int").
# Muestra los contactos que le fueron derivados y permite atenderlos o no atenderlos.

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.models.contacto_publico import ContactoPublico
from app.models.familiar import Familiar
from app.models.rol import Rol
from app.models.terapeuta import Terapeuta
from app.models.usuario import Usuario

router = APIRouter(
    prefix="/ter-int/contactos",
    tags=["Terapeuta interno — Contactos derivados"],
    dependencies=[Depends(require_roles("ter-int"))],
)

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Schemas ───────────────────────────────────────────────────────────────────

class ContactoDerivadoRead(BaseModel):
    id: str
    nombre: str
    celular: Optional[str]
    mail: Optional[str]
    comentario: Optional[str]
    mensaje_alerta: str
    respuesta_ia: str
    estado: str
    nota_derivacion: Optional[str]
    derivado_en: Optional[datetime]
    creado_en: datetime
    usuario_familiar_id: Optional[str] = None  # si ya fue atendido

    model_config = {"from_attributes": True}


class AtenderRequest(BaseModel):
    nombre: str
    apellido: Optional[str] = None
    email: str
    password: Optional[str] = None   # si no se provee se genera una temporal


# ── Helpers ───────────────────────────────────────────────────────────────────

def _contacto_dict(c: ContactoPublico, usuario_familiar_id: Optional[str] = None) -> dict:
    return {
        "id": str(c.id),
        "nombre": c.nombre,
        "celular": c.celular,
        "mail": c.mail,
        "comentario": c.comentario,
        "mensaje_alerta": c.mensaje_alerta,
        "respuesta_ia": c.respuesta_ia,
        "estado": c.estado,
        "nota_derivacion": c.nota_derivacion,
        "derivado_en": c.derivado_en,
        "creado_en": c.creado_en,
        "usuario_familiar_id": usuario_familiar_id,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", summary="Ver contactos derivados al terapeuta actual")
async def mis_contactos_derivados(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    estado: Optional[str] = None,   # derivado | atendido | no_atendido
):
    """
    Devuelve los contactos públicos que fueron derivados al terapeuta autenticado.
    Filtro opcional: ?estado=derivado  |  ?estado=atendido  |  ?estado=no_atendido
    """
    # Obtener el perfil Terapeuta del usuario actual
    ter_q = await db.execute(
        select(Terapeuta).where(Terapeuta.usuario_id == current_user.id)
    )
    terapeuta = ter_q.scalar_one_or_none()
    if not terapeuta:
        raise HTTPException(status_code=404, detail="No tenés perfil de terapeuta registrado")

    q = (
        select(ContactoPublico)
        .where(ContactoPublico.derivado_a_id == terapeuta.id)
        .order_by(ContactoPublico.derivado_en.desc())
    )
    if estado in ("derivado", "atendido", "rechazado"):
        q = q.where(ContactoPublico.estado == estado)
    else:
        # Por defecto mostrar todos los que llegaron al terapeuta
        q = q.where(ContactoPublico.estado.in_(["derivado", "atendido", "rechazado"]))

    result = await db.execute(q)
    contactos = result.scalars().all()
    return [_contacto_dict(c) for c in contactos]


@router.post("/{contacto_id}/atender", summary="Atender contacto: crear usuario familiar inactivo")
async def atender_contacto(
    contacto_id: UUID,
    body: AtenderRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Marca el contacto como 'atendido' y crea un usuario con rol familiar (inactivo).
    El familiar deberá activar su cuenta o ser activado por el admin.

    - Nombre y email son obligatorios.
    - Si ya existe un usuario con ese email, no crea uno nuevo pero marca el contacto.
    - La contraseña inicial es aleatoria (el usuario deberá resetearla al activarse).
    """
    # Verificar que el contacto existe y está derivado a este terapeuta
    ter_q = await db.execute(
        select(Terapeuta).where(Terapeuta.usuario_id == current_user.id)
    )
    terapeuta = ter_q.scalar_one_or_none()
    if not terapeuta:
        raise HTTPException(status_code=404, detail="No tenés perfil de terapeuta registrado")

    c_q = await db.execute(
        select(ContactoPublico).where(
            ContactoPublico.id == contacto_id,
            ContactoPublico.derivado_a_id == terapeuta.id,
        )
    )
    contacto = c_q.scalar_one_or_none()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado o no derivado a vos")

    if contacto.estado == "atendido":
        raise HTTPException(status_code=409, detail="Este contacto ya fue atendido")

    # Verificar email único
    email = body.email.strip().lower()
    existing_q = await db.execute(select(Usuario).where(Usuario.email == email))
    usuario_existente = existing_q.scalar_one_or_none()

    nuevo_usuario_id = None

    if usuario_existente:
        # El usuario ya existe — solo actualizar el estado del contacto
        nuevo_usuario_id = str(usuario_existente.id)
    else:
        # Obtener el rol "familia"
        rol_q = await db.execute(select(Rol).where(Rol.key == "familia"))
        rol_familia = rol_q.scalar_one_or_none()
        if not rol_familia:
            raise HTTPException(status_code=500, detail="Rol 'familia' no configurado")

        # Generar contraseña temporal si no se proveyó una
        import secrets as _sec
        sufijo = _sec.token_hex(3).upper()
        password_raw = body.password or f"Acc{sufijo}1!"
        nombre = body.nombre.strip()
        apellido = (body.apellido or "").strip()
        n = nombre[:1].upper()
        a = apellido[:1].upper() if apellido else ""

        nuevo_usuario = Usuario(
            id=uuid4(),
            email=email,
            nombre=nombre,
            apellido=apellido or None,
            password_hash=_pwd.hash(password_raw),
            rol_id=rol_familia.id,
            activo=True,                    # Activo de inmediato — recibe credenciales
            debe_cambiar_password=True,     # Debe cambiar la clave en el primer ingreso
            avatar_initials=f"{n}{a}" or "?",
            avatar_class="av-tl",
            profile_label="Familiar · Contacto TEA derivado",
        )
        db.add(nuevo_usuario)
        await db.flush()  # obtener el ID antes del commit

        # Crear perfil Familiar
        perfil_familiar = Familiar(
            id=uuid4(),
            usuario_id=nuevo_usuario.id,
            consentimiento_otorgado=False,
        )
        db.add(perfil_familiar)
        nuevo_usuario_id = str(nuevo_usuario.id)

    # Marcar contacto como atendido
    contacto.estado = "atendido"

    await db.commit()

    respuesta = {
        **_contacto_dict(contacto, usuario_familiar_id=nuevo_usuario_id),
        "mensaje": (
            "Usuario familiar creado. Recibirá sus credenciales para acceder al sistema."
            if not usuario_existente
            else "El email ya tenía cuenta registrada. Contacto marcado como atendido."
        ),
    }
    # Incluir contraseña temporal solo cuando se creó un usuario nuevo
    if not usuario_existente:
        respuesta["password_temporal"] = password_raw
        respuesta["nombre_familiar"]   = nombre
        respuesta["email_familiar"]    = email
    return respuesta


@router.post("/{contacto_id}/no-atender", summary="Marcar contacto como no atendido")
async def no_atender_contacto(
    contacto_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Marca el contacto como 'no_atendido'.
    El admin puede rederivarlo a otro terapeuta si es necesario.
    """
    ter_q = await db.execute(
        select(Terapeuta).where(Terapeuta.usuario_id == current_user.id)
    )
    terapeuta = ter_q.scalar_one_or_none()
    if not terapeuta:
        raise HTTPException(status_code=404, detail="No tenés perfil de terapeuta registrado")

    c_q = await db.execute(
        select(ContactoPublico).where(
            ContactoPublico.id == contacto_id,
            ContactoPublico.derivado_a_id == terapeuta.id,
        )
    )
    contacto = c_q.scalar_one_or_none()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado o no derivado a vos")

    if contacto.estado == "rechazado":
        raise HTTPException(status_code=409, detail="Este contacto ya fue rechazado")

    contacto.estado = "rechazado"
    await db.commit()

    return _contacto_dict(contacto)
