#!/usr/bin/env python3
"""
scripts/migrate_contactos.py
Migra la tabla contactos_publicos al schema actual.

Agrega las columnas que falten sin perder datos existentes:
  celular, mail, estado, derivado_a_id, nota_derivacion, derivado_en

También actualiza el nav_config del rol admin para incluir
los ítems nuevos (Contactos TEA, Reglas IA).

Uso:
    docker compose exec backend python scripts/migrate_contactos.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal, engine


# Columnas a agregar si no existen
COLUMNAS = [
    ("celular",          "VARCHAR(50)"),
    ("mail",             "VARCHAR(254)"),
    ("estado",           "VARCHAR(20) NOT NULL DEFAULT 'pendiente'"),
    ("derivado_a_id",    "UUID REFERENCES terapeutas(id) ON DELETE SET NULL"),
    ("nota_derivacion",  "TEXT"),
    ("derivado_en",      "TIMESTAMPTZ"),
]

ADMIN_NAV = [
    {"section": "Sistema", "items": [
        {"id": "admin-dash",      "icon": "home",       "label": "Panel de inicio"},
        {"id": "admin-usuarios",  "icon": "users",      "label": "Terapeutas"},
        {"id": "admin-contactos", "icon": "mail",       "label": "Contactos TEA"},
        {"id": "admin-reglas",    "icon": "shield",     "label": "Reglas IA"},
        {"id": "admin-auditoria", "icon": "bar-chart",  "label": "Auditoría"},
    ]},
]


async def migrar_contactos():
    print("\n══════════════════════════════════════════")
    print("  Migración: contactos_publicos")
    print("══════════════════════════════════════════")

    async with engine.begin() as conn:
        # Verificar que la tabla existe
        existe = await conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'contactos_publicos')"
        ))
        if not existe.scalar():
            print("  ℹ️  Tabla contactos_publicos no existe — se creará en el arranque")
        else:
            for columna, tipo in COLUMNAS:
                col_existe = await conn.execute(text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                    f"WHERE table_name='contactos_publicos' AND column_name='{columna}')"
                ))
                if col_existe.scalar():
                    print(f"  ✓  {columna} ya existe")
                else:
                    await conn.execute(text(
                        f"ALTER TABLE contactos_publicos ADD COLUMN {columna} {tipo}"
                    ))
                    print(f"  ✅ {columna} agregada")


async def actualizar_nav_admin():
    print("\n══════════════════════════════════════════")
    print("  Actualización: nav_config admin")
    print("══════════════════════════════════════════")

    import json
    from sqlalchemy.orm.attributes import flag_modified

    # Importar modelos después de sys.path
    from app.models.rol import Rol
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Rol).where(Rol.key == "admin"))
        rol = result.scalar_one_or_none()
        if not rol:
            print("  ⚠️  Rol 'admin' no encontrado")
            return
        rol.nav_config = ADMIN_NAV
        flag_modified(rol, "nav_config")
        await session.commit()
        print("  ✅ nav_config del admin actualizado")
        items = ADMIN_NAV[0]["items"]
        for item in items:
            print(f"       · {item['label']}")


async def main():
    await migrar_contactos()
    await actualizar_nav_admin()
    print("\n  🎯 Migraciones completadas. Reiniciá el backend para aplicar todos los cambios.")
    print()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
