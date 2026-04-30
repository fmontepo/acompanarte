# app/api/regla_ia_router.py
# CRUD de reglas de comportamiento para el Asistente IA
# Solo accesible para administradores.
#
# Reglas positivas → qué puede y debe responder el modelo
# Reglas negativas → qué no puede responder ni hacer
#
# Las reglas activas se cargan en cada request al pipeline RAG
# y se inyectan en el prompt antes de enviar a Ollama.

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.regla_ia import ReglaIA

router = APIRouter(
    prefix="/admin/reglas-ia",
    tags=["Admin — Reglas IA"],
    dependencies=[Depends(require_roles("admin"))],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class ReglaCreate(BaseModel):
    tipo: str           # 'positiva' | 'negativa'
    contexto: str = "global"   # 'familiar' | 'terapeuta' | 'global'
    texto: str
    descripcion: Optional[str] = None
    activa: bool = True
    orden: int = 0


class ReglaUpdate(BaseModel):
    texto: Optional[str] = None
    descripcion: Optional[str] = None
    contexto: Optional[str] = None
    activa: Optional[bool] = None
    orden: Optional[int] = None


def _serialize(r: ReglaIA) -> dict:
    return {
        "id":          str(r.id),
        "tipo":        r.tipo,
        "contexto":    r.contexto,
        "texto":       r.texto,
        "descripcion": r.descripcion,
        "activa":      r.activa,
        "orden":       r.orden,
        "creado_en":   r.creado_en,
        "actualizado_en": r.actualizado_en,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", summary="Listar reglas de IA")
async def listar_reglas(
    tipo: Optional[str] = None,         # positiva | negativa
    contexto: Optional[str] = None,     # familiar | terapeuta | global
    solo_activas: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(ReglaIA).order_by(ReglaIA.contexto, ReglaIA.tipo, ReglaIA.orden, ReglaIA.creado_en)
    if tipo in ("positiva", "negativa"):
        q = q.where(ReglaIA.tipo == tipo)
    if contexto in ("familiar", "terapeuta", "global"):
        q = q.where(ReglaIA.contexto == contexto)
    if solo_activas:
        q = q.where(ReglaIA.activa == True)
    result = await db.execute(q)
    return [_serialize(r) for r in result.scalars().all()]


@router.post("", summary="Crear regla de IA", status_code=201)
async def crear_regla(
    body: ReglaCreate,
    db: AsyncSession = Depends(get_db),
):
    if body.tipo not in ("positiva", "negativa"):
        raise HTTPException(400, detail="tipo debe ser 'positiva' o 'negativa'")
    if body.contexto not in ("familiar", "terapeuta", "global"):
        raise HTTPException(400, detail="contexto debe ser 'familiar', 'terapeuta' o 'global'")
    if not body.texto.strip():
        raise HTTPException(400, detail="El texto de la regla no puede estar vacío")

    regla = ReglaIA(
        tipo=body.tipo,
        contexto=body.contexto,
        texto=body.texto.strip(),
        descripcion=body.descripcion.strip() if body.descripcion else None,
        activa=body.activa,
        orden=body.orden,
    )
    db.add(regla)
    await db.commit()
    await db.refresh(regla)
    return _serialize(regla)


@router.patch("/{regla_id}", summary="Editar regla de IA")
async def editar_regla(
    regla_id: UUID,
    body: ReglaUpdate,
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
    if body.contexto is not None:
        if body.contexto not in ("familiar", "terapeuta", "global"):
            raise HTTPException(400, detail="contexto debe ser 'familiar', 'terapeuta' o 'global'")
        regla.contexto = body.contexto
    if body.activa is not None:
        regla.activa = body.activa
    if body.orden is not None:
        regla.orden = body.orden

    await db.commit()
    await db.refresh(regla)
    return _serialize(regla)


@router.delete("/{regla_id}", summary="Eliminar regla de IA", status_code=204)
async def eliminar_regla(
    regla_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ReglaIA).where(ReglaIA.id == regla_id))
    regla = result.scalar_one_or_none()
    if not regla:
        raise HTTPException(404, detail="Regla no encontrada")
    await db.delete(regla)
    await db.commit()
