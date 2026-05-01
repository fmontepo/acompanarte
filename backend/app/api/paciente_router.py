# app/api/paciente_router.py
# Gestión de pacientes — accesible para admin y terapeuta interno
# Los nombres se almacenan en nombre_enc (cifrado AES en producción completa)
# Por consistencia con el resto del sistema, se almacena el texto directamente
# hasta que el módulo de cifrado esté integrado a nivel servicio.

from datetime import date
from typing import Optional, List
from uuid import UUID
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.models.paciente import Paciente
from app.models.familiar import Familiar
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.vinculoPaciente import VinculoPaciente
from app.models.parentesco import Parentesco

router = APIRouter(
    prefix="/pacientes",
    tags=["Pacientes"],
    dependencies=[Depends(require_roles("admin", "ter-int"))],
)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class PacienteIn(BaseModel):
    nombre: str
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None          # M | F | X


class PacientePatch(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None
    activo: Optional[bool] = None


class VincularFamiliarIn(BaseModel):
    familiar_id: str       # UUID del Familiar (no del Usuario)
    id_parentesco: str     # código ej: MA, PA, AB
    es_tutor_legal: bool = False
    autorizado_medico: bool = False


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _calcular_edad(fn) -> Optional[int]:
    if not fn:
        return None
    hoy = date.today()
    años = hoy.year - fn.year
    if (hoy.month, hoy.day) < (fn.month, fn.day):
        años -= 1
    return años


def _paciente_dict(p: Paciente) -> dict:
    vinculos = []
    for v in (p.vinculos or []):
        fam = v.familiar
        if not fam:
            continue
        u = fam.usuario
        vinculos.append({
            "vinculo_id":       str(v.id),
            "familiar_id":      str(fam.id),
            "usuario_id":       str(fam.usuario_id),
            "nombre_familiar":  (f"{u.nombre or ''} {u.apellido or ''}".strip() or u.email) if u else "—",
            "email":            u.email if u else None,
            "parentesco":       v.id_parentesco,
            "parentesco_nombre": v.parentesco.nombre if v.parentesco else v.id_parentesco,
            "es_tutor_legal":   v.es_tutor_legal,
            "autorizado_medico": v.autorizado_medico,
            "activo":           v.activo,
        })
    return {
        "id":               str(p.id),
        "nombre":           p.nombre_enc or "—",
        "apellido":         p.apellido_enc or None,
        "fecha_nacimiento": p.fecha_nacimiento.isoformat() if p.fecha_nacimiento else None,
        "edad":             _calcular_edad(p.fecha_nacimiento),
        "sexo":             p.sexo,
        "nivel_soporte":    p.nivel_soporte,
        "activo":           p.activo,
        "creado_en":        p.creado_en.isoformat() if p.creado_en else None,
        "vinculos":         vinculos,
    }


# ─── Endpoints de catálogo (rutas fijas — ANTES de /{id}) ────────────────────

@router.get(
    "/parentescos",
    summary="Catálogo de tipos de parentesco",
    dependencies=[],  # sobreescribe — acceso libre para familiares también
)
async def listar_parentescos(db: AsyncSession = Depends(get_db)):
    """Devuelve el catálogo de parentescos disponible."""
    result = await db.execute(select(Parentesco).order_by(Parentesco.nombre))
    return [{"id": p.id_parentesco, "nombre": p.nombre} for p in result.scalars().all()]


@router.get(
    "/familiares-disponibles",
    summary="Usuarios con rol familia disponibles para vincular",
)
async def familiares_disponibles(db: AsyncSession = Depends(get_db)):
    """
    Devuelve todos los usuarios con rol 'familia' activos que tienen perfil Familiar.
    Se usa para el selector al vincular un familiar a un paciente.
    """
    result = await db.execute(
        select(Familiar)
        .options(joinedload(Familiar.usuario))
        .join(Usuario, Familiar.usuario_id == Usuario.id)
        .where(Usuario.activo == True)
        .order_by(Usuario.nombre, Usuario.apellido)
    )
    familiares = result.unique().scalars().all()
    lista = []
    for f in familiares:
        u = f.usuario
        if not u:
            continue
        lista.append({
            "familiar_id":    str(f.id),
            "usuario_id":     str(u.id),
            "nombre_completo": f"{u.nombre or ''} {u.apellido or ''}".strip() or u.email,
            "email":          u.email,
        })
    return lista


# ─── CRUD de pacientes ───────────────────────────────────────────────────────

@router.get("/", summary="Listar todos los pacientes")
async def listar_pacientes(
    db: AsyncSession = Depends(get_db),
    activos_solo: bool = True,
):
    q = (
        select(Paciente)
        .options(
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.familiar)
            .selectinload(Familiar.usuario),
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.parentesco),
        )
        .order_by(Paciente.creado_en.desc())
    )
    if activos_solo:
        q = q.where(Paciente.activo == True)
    result = await db.execute(q)
    pacientes = result.unique().scalars().all()
    return [_paciente_dict(p) for p in pacientes]


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Crear nuevo paciente")
async def crear_paciente(
    data: PacienteIn,
    db: AsyncSession = Depends(get_db),
):
    """Crea un paciente nuevo. El nombre se almacena en nombre_enc."""
    if not data.nombre.strip():
        raise HTTPException(status_code=422, detail="El nombre del paciente es obligatorio.")
    if data.sexo and data.sexo not in {"M", "F", "X"}:
        raise HTTPException(status_code=422, detail="Sexo inválido. Usá M, F o X.")

    paciente = Paciente(
        id=_uuid.uuid4(),
        nombre_enc=data.nombre.strip(),
        apellido_enc=data.apellido.strip() if data.apellido else None,
        fecha_nacimiento=data.fecha_nacimiento,
        sexo=data.sexo,
        activo=True,
    )
    db.add(paciente)
    await db.commit()
    await db.refresh(paciente)

    # Recargar con vinculos (vacío al crear, pero mantiene la forma de respuesta)
    result = await db.execute(
        select(Paciente)
        .options(
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.familiar)
            .selectinload(Familiar.usuario),
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.parentesco),
        )
        .where(Paciente.id == paciente.id)
    )
    return _paciente_dict(result.unique().scalar_one())


@router.get("/{paciente_id}", summary="Detalle de un paciente")
async def obtener_paciente(
    paciente_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Paciente)
        .options(
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.familiar)
            .selectinload(Familiar.usuario),
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.parentesco),
        )
        .where(Paciente.id == paciente_id)
    )
    p = result.unique().scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
    return _paciente_dict(p)


@router.patch("/{paciente_id}", summary="Actualizar datos del paciente")
async def actualizar_paciente(
    paciente_id: UUID,
    data: PacientePatch,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Paciente).where(Paciente.id == paciente_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")

    if data.nombre is not None:
        p.nombre_enc = data.nombre.strip()
    if data.apellido is not None:
        p.apellido_enc = data.apellido.strip() or None
    if data.fecha_nacimiento is not None:
        p.fecha_nacimiento = data.fecha_nacimiento
    if data.sexo is not None:
        if data.sexo not in {"M", "F", "X", ""}:
            raise HTTPException(status_code=422, detail="Sexo inválido.")
        p.sexo = data.sexo or None
    if data.activo is not None:
        p.activo = data.activo

    await db.commit()

    result2 = await db.execute(
        select(Paciente)
        .options(
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.familiar)
            .selectinload(Familiar.usuario),
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.parentesco),
        )
        .where(Paciente.id == paciente_id)
    )
    return _paciente_dict(result2.unique().scalar_one())


# ─── Vínculos paciente ↔ familiar ────────────────────────────────────────────

@router.post(
    "/{paciente_id}/vincular-familiar",
    status_code=status.HTTP_201_CREATED,
    summary="Vincular un familiar a un paciente",
)
async def vincular_familiar(
    paciente_id: UUID,
    data: VincularFamiliarIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea el vínculo Familiar → Paciente con el tipo de parentesco y permisos.
    Verifica que el paciente y el familiar existan.
    """
    # Verificar paciente
    p_result = await db.execute(select(Paciente).where(Paciente.id == paciente_id))
    if not p_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")

    # Verificar familiar
    try:
        fam_uuid = UUID(data.familiar_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="familiar_id inválido.")
    f_result = await db.execute(select(Familiar).where(Familiar.id == fam_uuid))
    if not f_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Familiar no encontrado.")

    # Verificar parentesco válido
    par_result = await db.execute(
        select(Parentesco).where(Parentesco.id_parentesco == data.id_parentesco)
    )
    if not par_result.scalar_one_or_none():
        raise HTTPException(status_code=422, detail=f"Parentesco '{data.id_parentesco}' no existe.")

    # Evitar duplicado activo
    dup = await db.execute(
        select(VinculoPaciente).where(
            VinculoPaciente.paciente_id == paciente_id,
            VinculoPaciente.familiar_id == fam_uuid,
            VinculoPaciente.activo == True,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Este familiar ya está vinculado al paciente.")

    vinculo = VinculoPaciente(
        id=_uuid.uuid4(),
        paciente_id=paciente_id,
        familiar_id=fam_uuid,
        id_parentesco=data.id_parentesco,
        es_tutor_legal=data.es_tutor_legal,
        autorizado_medico=data.autorizado_medico,
        activo=True,
    )
    db.add(vinculo)
    await db.commit()

    # Retornar paciente actualizado
    result = await db.execute(
        select(Paciente)
        .options(
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.familiar)
            .selectinload(Familiar.usuario),
            selectinload(Paciente.vinculos)
            .selectinload(VinculoPaciente.parentesco),
        )
        .where(Paciente.id == paciente_id)
    )
    return _paciente_dict(result.unique().scalar_one())


@router.delete(
    "/{paciente_id}/vinculos/{vinculo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desvincular un familiar de un paciente",
)
async def desvincular_familiar(
    paciente_id: UUID,
    vinculo_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VinculoPaciente).where(
            VinculoPaciente.id == vinculo_id,
            VinculoPaciente.paciente_id == paciente_id,
        )
    )
    vinculo = result.scalar_one_or_none()
    if not vinculo:
        raise HTTPException(status_code=404, detail="Vínculo no encontrado.")
    vinculo.activo = False
    await db.commit()
