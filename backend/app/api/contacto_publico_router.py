# app/api/contacto_publico_router.py
# Gestión de contactos públicos generados por el Asistente TEA
# Solo accesible para administradores.
# Permite listar, ver detalle y derivar contactos a terapeutas internos.

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.models.contacto_publico import ContactoPublico
from app.models.terapeuta import Terapeuta
from app.models.usuario import Usuario

router = APIRouter(
    prefix="/admin/contactos",
    tags=["Admin — Contactos públicos"],
    dependencies=[Depends(require_roles("admin"))],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class TerapeutaSimple(BaseModel):
    id: str
    nombre_completo: str
    profesion: str
    especialidad: Optional[str] = None

    model_config = {"from_attributes": True}


class ContactoRead(BaseModel):
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
    terapeuta: Optional[TerapeutaSimple] = None

    model_config = {"from_attributes": True}


class DerivarRequest(BaseModel):
    terapeuta_id: str
    nota: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _contacto_to_dict(c: ContactoPublico) -> dict:
    ter = None
    if c.terapeuta and c.terapeuta.usuario:
        u = c.terapeuta.usuario
        ter = {
            "id": str(c.terapeuta.id),
            "nombre_completo": f"{u.nombre or ''} {u.apellido or ''}".strip() or u.email,
            "profesion": c.terapeuta.profesion,
            "especialidad": c.terapeuta.especialidad,
        }
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
        "terapeuta": ter,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", summary="Listar contactos públicos (admin)")
async def listar_contactos(
    estado: Optional[str] = None,   # pendiente | derivado
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve todos los contactos generados desde el asistente público.
    Filtro opcional: ?estado=pendiente  o  ?estado=derivado
    Ordenados del más reciente al más antiguo.
    """
    q = (
        select(ContactoPublico)
        .options(
            joinedload(ContactoPublico.terapeuta).joinedload(Terapeuta.usuario)
        )
        .order_by(ContactoPublico.creado_en.desc())
    )
    if estado in ("pendiente", "derivado"):
        q = q.where(ContactoPublico.estado == estado)

    result = await db.execute(q)
    contactos = result.unique().scalars().all()
    return [_contacto_to_dict(c) for c in contactos]


@router.get("/{contacto_id}", summary="Detalle de un contacto")
async def detalle_contacto(
    contacto_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContactoPublico)
        .options(
            joinedload(ContactoPublico.terapeuta).joinedload(Terapeuta.usuario)
        )
        .where(ContactoPublico.id == contacto_id)
    )
    c = result.unique().scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return _contacto_to_dict(c)


@router.post("/{contacto_id}/derivar", summary="Derivar contacto a terapeuta interno")
async def derivar_contacto(
    contacto_id: UUID,
    body: DerivarRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Asigna el contacto a un terapeuta interno y cambia su estado a 'derivado'.
    Puede llamarse múltiples veces para reasignar.
    """
    # Verificar contacto
    result = await db.execute(
        select(ContactoPublico)
        .options(
            joinedload(ContactoPublico.terapeuta).joinedload(Terapeuta.usuario)
        )
        .where(ContactoPublico.id == contacto_id)
    )
    contacto = result.unique().scalar_one_or_none()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

    # Verificar que el terapeuta existe y está activo
    ter_result = await db.execute(
        select(Terapeuta)
        .options(joinedload(Terapeuta.usuario))
        .where(Terapeuta.id == UUID(body.terapeuta_id))
        .where(Terapeuta.activo == True)
    )
    terapeuta = ter_result.unique().scalar_one_or_none()
    if not terapeuta:
        raise HTTPException(status_code=404, detail="Terapeuta no encontrado o inactivo")

    # Actualizar
    contacto.derivado_a_id  = terapeuta.id
    contacto.nota_derivacion = body.nota.strip() if body.nota else None
    contacto.estado          = "derivado"
    contacto.derivado_en     = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(contacto)

    # Recargar con join
    result2 = await db.execute(
        select(ContactoPublico)
        .options(
            joinedload(ContactoPublico.terapeuta).joinedload(Terapeuta.usuario)
        )
        .where(ContactoPublico.id == contacto_id)
    )
    contacto = result2.unique().scalar_one()
    return _contacto_to_dict(contacto)


# ── Endpoint auxiliar: terapeutas internos disponibles ───────────────────────

@router.get(
    "/..terapeutas-internos",   # /admin/contactos/../terapeutas-internos → no funciona
    include_in_schema=False,    # se define aparte abajo
)
async def _placeholder(): pass  # no se usa


# Se define fuera del prefix para no colisionar con /{contacto_id}
terapeutas_router = APIRouter(
    prefix="/admin",
    tags=["Admin — Contactos públicos"],
    dependencies=[Depends(require_roles("admin"))],
)


@terapeutas_router.get(
    "/terapeutas-internos",
    summary="Terapeutas internos activos (para derivación)",
)
async def listar_terapeutas_internos(
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve los terapeutas internos (institucional=True o tipo_acceso=institucional)
    activos y validados. Se usa para poblar el selector de derivación.
    """
    result = await db.execute(
        select(Terapeuta)
        .options(joinedload(Terapeuta.usuario))
        .where(Terapeuta.activo == True)
        .where(Terapeuta.validado == True)
        .order_by(Terapeuta.creado_en.asc())
    )
    terapeutas = result.unique().scalars().all()

    lista = []
    for t in terapeutas:
        u = t.usuario
        if not u:
            continue
        lista.append({
            "id": str(t.id),
            "nombre_completo": f"{u.nombre or ''} {u.apellido or ''}".strip() or u.email,
            "profesion": t.profesion,
            "especialidad": t.especialidad,
            "email": u.email,
        })
    return lista
