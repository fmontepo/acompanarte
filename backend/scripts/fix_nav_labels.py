#!/usr/bin/env python3
"""
scripts/fix_nav_labels.py
Actualiza el nav_config del rol admin en la BD:
  - "Terapeutas" → "Usuarios" en el ítem admin-usuarios

Uso:
    docker compose -f docker-compose.prod.yml --env-file .env.prod \
        exec -T backend python scripts/fix_nav_labels.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import select
from app.db.session import AsyncSessionLocal


ADMIN_NAV = [
    {"section": "Sistema", "items": [
        {"id": "admin-dash",      "icon": "home",       "label": "Panel de inicio"},
        {"id": "admin-usuarios",  "icon": "users",      "label": "Usuarios"},
        {"id": "admin-contactos", "icon": "mail",       "label": "Contactos TEA"},
        {"id": "admin-reglas",    "icon": "shield",     "label": "Reglas IA"},
        {"id": "admin-auditoria", "icon": "bar-chart",  "label": "Auditoría"},
    ]},
]


async def main():
    from app.models.rol import Rol  # noqa: evita circular import al inicio

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Rol).where(Rol.key == "admin"))
        rol = result.scalar_one_or_none()
        if not rol:
            print("❌ Rol 'admin' no encontrado.")
            return
        rol.nav_config = ADMIN_NAV
        flag_modified(rol, "nav_config")
        await session.commit()
        print("✅ nav_config del admin actualizado:")
        for item in ADMIN_NAV[0]["items"]:
            print(f"   · {item['label']}")
        print("\nEl admin debe cerrar sesión y volver a ingresar para ver el cambio.")


if __name__ == "__main__":
    asyncio.run(main())
