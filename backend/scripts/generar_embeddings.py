#!/usr/bin/env python3
"""
scripts/generar_embeddings.py
─────────────────────────────
Genera (o regenera) los embeddings pgvector para todos los recursos
profesionales validados que tengan contenido_texto y no tengan embedding.

Uso:
    docker compose exec backend python scripts/generar_embeddings.py
    docker compose exec backend python scripts/generar_embeddings.py --todos   # regenera todos
    docker compose exec backend python scripts/generar_embeddings.py --dry-run # muestra qué haría

El script es idempotente: si se corre dos veces, la segunda no hace nada
(salvo que uses --todos para regenerar todos los embeddings).
"""

import asyncio
import sys
import os
import time

# Asegurar que el path del proyecto está en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func

# Importar TODOS los modelos antes de usar cualquiera.
# SQLAlchemy necesita resolver todas las relaciones (relationship()) juntas.
# Sin esto, los imports parciales causan circular import errors.
from app.db.base import Base                                    # noqa: F401
from app.models.rol import Rol                                  # noqa: F401
from app.models.usuario import Usuario                          # noqa: F401
from app.models.familiar import Familiar                        # noqa: F401
from app.models.terapeuta import Terapeuta                      # noqa: F401
from app.models.administrador import Administrador              # noqa: F401
from app.models.paciente import Paciente                        # noqa: F401
from app.models.parentesco import Parentesco                    # noqa: F401
from app.models.vinculoPaciente import VinculoPaciente          # noqa: F401
from app.models.actividadFamiliar import ActividadFamiliar      # noqa: F401
from app.models.registroSeguimiento import RegistroSeguimiento  # noqa: F401
from app.models.alerta import Alerta                            # noqa: F401
from app.models.ia import SesionIA, MensajeIA                  # noqa: F401
from app.models.recursoProfesional import RecursoProfesional

# ---------------------------------------------------------------------------
# Configuración de BD (igual que el backend)
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://acomp_user:cambia_esto_en_produccion@db:5432/acompanarte_db"
)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Carga del modelo de embeddings (singleton)
# ---------------------------------------------------------------------------
def cargar_modelo():
    print(f"⏳ Cargando modelo de embeddings: {EMBEDDING_MODEL_NAME}")
    print("   (La primera vez puede tardar varios minutos mientras se descarga)")
    t0 = time.time()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    elapsed = time.time() - t0
    dim = model.get_sentence_embedding_dimension()
    print(f"   ✓ Modelo cargado en {elapsed:.1f}s — dimensión: {dim}")
    return model


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------
async def generar_embeddings(regenerar_todos: bool = False, dry_run: bool = False):
    print()
    print("═" * 58)
    print("  📐  Generador de Embeddings — Acompañarte RAG")
    print("═" * 58)
    print()

    async with AsyncSessionLocal() as db:

        # ── Consultar recursos candidatos ──────────────────────────────
        query = (
            select(RecursoProfesional)
            .where(RecursoProfesional.validado == True)
            .where(RecursoProfesional.activo == True)
            .where(RecursoProfesional.contenido_texto.is_not(None))
        )
        if not regenerar_todos:
            query = query.where(RecursoProfesional.embedding.is_(None))

        result = await db.execute(query)
        recursos = result.scalars().all()

        if not recursos:
            if regenerar_todos:
                print("ℹ️  No hay recursos validados con contenido_texto.")
            else:
                print("✅  Todos los recursos ya tienen embeddings. Nada que hacer.")
                print("    Usá --todos para regenerar todos los embeddings.\n")
            return

        # ── Estadísticas ───────────────────────────────────────────────
        total_q = await db.execute(
            select(func.count(RecursoProfesional.id))
            .where(RecursoProfesional.validado == True)
            .where(RecursoProfesional.activo == True)
        )
        total = total_q.scalar_one()

        sin_content_q = await db.execute(
            select(func.count(RecursoProfesional.id))
            .where(RecursoProfesional.validado == True)
            .where(RecursoProfesional.activo == True)
            .where(RecursoProfesional.contenido_texto.is_(None))
        )
        sin_content = sin_content_q.scalar_one()

        print(f"  Recursos validados totales:           {total}")
        print(f"  Sin contenido_texto (no procesables): {sin_content}")
        print(f"  A procesar ahora:                     {len(recursos)}")
        print()

        if dry_run:
            print("🔍 DRY RUN — Los siguientes recursos serían procesados:")
            for r in recursos:
                chars = len(r.contenido_texto) if r.contenido_texto else 0
                print(f"   • {r.titulo[:55]:<55} ({chars} chars)")
            print()
            return

        # ── Cargar modelo ──────────────────────────────────────────────
        model = cargar_modelo()
        print()

        # ── Generar embeddings ─────────────────────────────────────────
        ok = 0
        errores = 0
        t_total = time.time()

        for i, recurso in enumerate(recursos, 1):
            try:
                t0 = time.time()

                # Construir el texto a embeddear: título + descripción + contenido
                partes = [recurso.titulo]
                if recurso.descripcion:
                    partes.append(recurso.descripcion)
                partes.append(recurso.contenido_texto)
                texto = "\n\n".join(partes)

                # Generar embedding
                embedding = model.encode(texto).tolist()
                recurso.embedding = embedding

                elapsed = time.time() - t0
                chars = len(texto)
                print(f"  [{i:>2}/{len(recursos)}] ✓ {recurso.titulo[:48]:<48}  {chars:>5} chars  {elapsed:.2f}s")
                ok += 1

            except Exception as e:
                print(f"  [{i:>2}/{len(recursos)}] ✗ {recurso.titulo[:48]} — ERROR: {e}")
                errores += 1

        # ── Guardar en BD ──────────────────────────────────────────────
        await db.commit()
        elapsed_total = time.time() - t_total

        print()
        print("─" * 58)
        print(f"  ✅  Completado en {elapsed_total:.1f}s")
        print(f"      Embeddings generados: {ok}")
        if errores:
            print(f"      ⚠ Errores:             {errores}")
        print()

        # ── Verificación final ─────────────────────────────────────────
        con_emb_q = await db.execute(
            select(func.count(RecursoProfesional.id))
            .where(RecursoProfesional.validado == True)
            .where(RecursoProfesional.activo == True)
            .where(RecursoProfesional.embedding.is_not(None))
        )
        con_emb = con_emb_q.scalar_one()
        print(f"  Recursos con embedding en BD: {con_emb} / {total}")
        print()

        if con_emb < total - sin_content:
            print("  ⚠  Aún hay recursos sin embedding (posiblemente sin contenido_texto).")
            print("     Subí el contenido desde Conocimiento → Nuevo recurso → campo Texto.")
        else:
            print("  🎯 Base de conocimiento RAG lista para uso.")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    regenerar_todos = "--todos" in sys.argv or "--all" in sys.argv
    dry_run         = "--dry-run" in sys.argv or "--dry" in sys.argv

    if regenerar_todos:
        print("⚠️  Modo --todos: se regenerarán TODOS los embeddings (incluso existentes).")

    asyncio.run(generar_embeddings(
        regenerar_todos=regenerar_todos,
        dry_run=dry_run,
    ))
