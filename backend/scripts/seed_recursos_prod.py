#!/usr/bin/env python3
"""
scripts/seed_recursos_prod.py
──────────────────────────────────────────────────────────────────────────────
Carga los recursos profesionales (base de conocimiento TEA) en producción.
NO crea usuarios demo, pacientes ni datos de prueba.

Uso en el servidor:
    docker compose -f docker-compose.prod.yml --env-file .env.prod \
        exec -T backend python scripts/seed_recursos_prod.py

Luego generar embeddings:
    docker compose -f docker-compose.prod.yml --env-file .env.prod \
        exec -T backend python scripts/generar_embeddings.py
──────────────────────────────────────────────────────────────────────────────
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.db.base import Base          # noqa: F401 — resuelve todas las relaciones ORM
from app.models.rol import Rol        # noqa: F401
from app.models.usuario import Usuario
from app.models.recursoProfesional import RecursoProfesional

# ── Importar los recursos desde seed.py (fuente única de verdad) ──────────
from seed import RECURSOS_DEMO

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://acomp_user:cambia_esto@db:5432/acompanarte_db"
)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with Session() as db:
        # Buscar el usuario admin para asignarlo como subidor/validador
        result = await db.execute(
            select(Usuario).where(
                Usuario.activo == True
            ).limit(1)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            print("❌ No se encontró ningún usuario activo. Ejecutá el deploy --first primero.")
            return

        print(f"✓ Usando usuario '{admin.email}' como subidor/validador")

        # Verificar cuántos recursos ya existen
        count_result = await db.execute(select(RecursoProfesional))
        existentes = count_result.scalars().all()

        if existentes:
            print(f"⚠️  Ya existen {len(existentes)} recursos en la base de datos.")
            print("   Para evitar duplicados, el script se detiene aquí.")
            print("   Si querés recargar, borrá los recursos desde la BD primero.")
            return

        # Cargar los recursos
        print(f"\n📚 Cargando {len(RECURSOS_DEMO)} recursos profesionales...")
        ahora = datetime.now(timezone.utc)

        for r_data in RECURSOS_DEMO:
            recurso = RecursoProfesional(
                subido_por=admin.id,
                validado_por=admin.id if r_data["validado"] else None,
                titulo=r_data["titulo"],
                descripcion=r_data["descripcion"],
                tipo=r_data["tipo"],
                contenido_texto=r_data.get("contenido_texto"),
                validado=r_data["validado"],
                activo=True,
                validado_en=ahora if r_data["validado"] else None,
            )
            db.add(recurso)
            estado = "✓ validado" if r_data["validado"] else "  pendiente"
            print(f"   [{estado}] {r_data['titulo'][:60]}")

        await db.commit()
        validados = sum(1 for r in RECURSOS_DEMO if r["validado"])
        print(f"\n✅ {len(RECURSOS_DEMO)} recursos cargados ({validados} validados, listos para RAG)")
        print("\nPróximo paso — generar embeddings:")
        print("  docker compose -f docker-compose.prod.yml --env-file .env.prod \\")
        print("      exec -T backend python scripts/generar_embeddings.py")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
