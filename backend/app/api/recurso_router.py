# app/api/recurso_router.py
# Gestión de recursos bibliográficos para el RAG
# Flujo: terapeuta sube → admin/terapeuta senior valida → RAG lo indexa
# Solo recursos con validado=True alimentan el sistema RAG

import asyncio
import logging
from typing import List
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db, AsyncSessionLocal
from app.models.recursoProfesional import RecursoProfesional
from app.schemas.recurso_profesional import RecursoCreate, RecursoRead
from app.api.deps import CurrentUser, require_roles

log = logging.getLogger(__name__)

router = APIRouter(prefix="/recursos", tags=["Recursos profesionales"])


# ---------------------------------------------------------------------------
# Background task: genera el embedding RAG después de validar el recurso.
# Corre en un thread separado para no bloquear el event loop ni la respuesta
# HTTP. Abre su propia sesión de DB (la del request ya está cerrada).
# ---------------------------------------------------------------------------
async def _generar_embedding_background(recurso_id: UUID, texto_completo: str) -> None:
    log.info("[Embedding] Iniciando para recurso %s", recurso_id)
    try:
        from app.services.ia_service import get_embedding_model
        model = get_embedding_model()
        # encode() es sincrónico — ejecutar en thread pool para no bloquear
        embedding = await asyncio.to_thread(model.encode, texto_completo)
        vector = embedding.tolist()

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(RecursoProfesional).where(RecursoProfesional.id == recurso_id)
            )
            recurso = result.scalar_one_or_none()
            if recurso:
                recurso.embedding = vector
                await db.commit()
                log.info("[Embedding] Guardado correctamente para recurso %s", recurso_id)
            else:
                log.warning("[Embedding] Recurso %s no encontrado al guardar embedding", recurso_id)
    except Exception:
        log.exception("[Embedding] Error al generar embedding para recurso %s", recurso_id)


# ---------------------------------------------------------------------------
# GET /api/v1/recursos — listar recursos validados
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[RecursoRead],
    summary="Listar recursos validados disponibles para RAG",
)
async def listar_recursos(
    db: AsyncSession = Depends(get_db),
    solo_validados: bool = True,
    skip: int = 0,
    limit: int = 100,
):
    query = select(RecursoProfesional).where(
        RecursoProfesional.activo == True
    ).order_by(RecursoProfesional.subido_en.desc())

    if solo_validados:
        query = query.where(RecursoProfesional.validado == True)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


# ---------------------------------------------------------------------------
# POST /api/v1/recursos — subir nuevo recurso (terapeuta/admin)
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=RecursoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "ter-int", "ter-ext"))],
    summary="Subir nuevo recurso bibliográfico",
)
async def subir_recurso(
    data: RecursoCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    recurso = RecursoProfesional(
        titulo=data.titulo,
        descripcion=data.descripcion,
        tipo=data.tipo,
        url_storage=data.url_storage,
        contenido_texto=data.contenido_texto,   # Texto para generar embedding RAG
        subido_por=current_user.id,
        validado=False,     # Siempre False al subir — requiere validación
    )
    db.add(recurso)
    await db.commit()
    await db.refresh(recurso)
    return recurso


# ---------------------------------------------------------------------------
# GET /api/v1/recursos/{id} — detalle de un recurso
# ---------------------------------------------------------------------------
@router.get(
    "/{recurso_id}",
    response_model=RecursoRead,
    summary="Obtener detalle de un recurso",
)
async def obtener_recurso(
    recurso_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RecursoProfesional).where(RecursoProfesional.id == recurso_id)
    )
    recurso = result.scalar_one_or_none()
    if not recurso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso no encontrado"
        )
    return recurso


# ---------------------------------------------------------------------------
# POST /api/v1/recursos/{id}/validar — validar recurso (terapeuta/admin)
# Marca el recurso como validado para que el RAG lo indexe
# ---------------------------------------------------------------------------
@router.post(
    "/{recurso_id}/validar",
    response_model=RecursoRead,
    dependencies=[Depends(require_roles("admin", "ter-int"))],
    summary="Validar recurso para uso en RAG",
)
async def validar_recurso(
    recurso_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RecursoProfesional).where(RecursoProfesional.id == recurso_id)
    )
    recurso = result.scalar_one_or_none()

    if not recurso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso no encontrado"
        )

    if recurso.validado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El recurso ya está validado"
        )

    recurso.validado = True
    recurso.validado_por = current_user.id
    recurso.validado_en = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(recurso)

    # Encolar generación de embedding como tarea en background.
    # La respuesta HTTP se envía de inmediato; el embedding se genera en paralelo
    # (~15-30 s) sin bloquear al usuario ni al event loop.
    if recurso.contenido_texto:
        partes = [recurso.titulo]
        if recurso.descripcion:
            partes.append(recurso.descripcion)
        partes.append(recurso.contenido_texto)
        texto_completo = "\n\n".join(partes)
        background_tasks.add_task(_generar_embedding_background, recurso.id, texto_completo)
        log.info("[Validar] Embedding para recurso %s encolado en background", recurso.id)

    return recurso


# ---------------------------------------------------------------------------
# DELETE /api/v1/recursos/{id} — desactivar recurso (admin)
# ---------------------------------------------------------------------------
@router.delete(
    "/{recurso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
    summary="Desactivar recurso (soft delete)",
)
async def desactivar_recurso(
    recurso_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RecursoProfesional).where(RecursoProfesional.id == recurso_id)
    )
    recurso = result.scalar_one_or_none()

    if not recurso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso no encontrado"
        )

    recurso.activo = False
    await db.commit()
