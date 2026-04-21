"""
init_prod.py — Inicialización mínima para entorno de producción
===============================================================
Este script prepara el sistema para su primer uso real.
NO borra datos existentes. Es seguro ejecutarlo múltiples veces (idempotente).

Qué hace:
  1. Crea las tablas si no existen (equivalente a alembic upgrade head)
  2. Crea los 4 roles del sistema si no existen
  3. Crea el catálogo de parentescos si no existe
  4. Crea el primer usuario administrador (configurable por variables de entorno
     o solicitado de forma interactiva si no están definidas)

Variables de entorno opcionales:
  ADMIN_EMAIL     Email del administrador (default: solicita interactivo)
  ADMIN_PASSWORD  Contraseña del administrador (default: solicita interactivo)
  ADMIN_NOMBRE    Nombre del administrador    (default: "Admin")
  ADMIN_APELLIDO  Apellido del administrador  (default: "Sistema")

Uso:
  # Modo interactivo:
  docker compose exec backend python init_prod.py

  # Modo desatendido (CI/CD):
  docker compose exec -e ADMIN_EMAIL=admin@miempresa.com \\
                      -e ADMIN_PASSWORD=SuperSecreto123 \\
                      backend python init_prod.py

  # O con .env ya configurado:
  docker compose exec backend python init_prod.py
"""

import asyncio
import getpass
import os
import re
import sys

from passlib.context import CryptContext
from sqlalchemy import select

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.administrador import Administrador
from app.models.parentesco import Parentesco

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGO DE ROLES
# ─────────────────────────────────────────────────────────────────────────────
ROLES = [
    {
        "key": "familia",
        "label": "Panel familiar",
        "default_path": "/familiar/dashboard",
        "nav_config": [
            {"section": "Principal", "items": [
                {"id": "dashboard",    "icon": "home",      "label": "Panel de inicio"},
                {"id": "seguimientos", "icon": "clipboard", "label": "Seguimientos"},
                {"id": "actividades",  "icon": "target",    "label": "Actividades"},
            ]},
            {"section": "Herramientas", "items": [
                {"id": "asistente", "icon": "bot",  "label": "Asistente IA"},
                {"id": "alertas",   "icon": "bell", "label": "Alertas", "badge": 0},
            ]},
        ],
    },
    {
        "key": "ter-int",
        "label": "Terapeuta interno",
        "default_path": "/terapeuta/interno/dashboard",
        "nav_config": [
            {"section": "Principal", "items": [
                {"id": "ter-int-dash",        "icon": "home",      "label": "Panel de inicio"},
                {"id": "ter-int-registros",   "icon": "pencil",    "label": "Registros"},
                {"id": "ter-int-actividades", "icon": "clipboard", "label": "Actividades"},
            ]},
            {"section": "Herramientas", "items": [
                {"id": "ter-int-conocimiento", "icon": "book", "label": "Base de conocimiento"},
                {"id": "alertas",              "icon": "bell", "label": "Alertas", "badge": 0},
            ]},
        ],
    },
    {
        "key": "ter-ext",
        "label": "Terapeuta externo",
        "default_path": "/terapeuta/externo/dashboard",
        "nav_config": [
            {"section": "Principal", "items": [
                {"id": "ter-ext-dash",      "icon": "home",   "label": "Panel de inicio"},
                {"id": "ter-ext-registros", "icon": "pencil", "label": "Mis registros"},
            ]},
        ],
    },
    {
        "key": "admin",
        "label": "Administración",
        "default_path": "/admin/dashboard",
        "nav_config": [
            {"section": "Sistema", "items": [
                {"id": "admin-dash",      "icon": "home",      "label": "Panel de inicio"},
                {"id": "admin-usuarios",  "icon": "users",     "label": "Terapeutas"},
                {"id": "admin-auditoria", "icon": "bar-chart", "label": "Auditoría"},
            ]},
        ],
    },
]

PARENTESCOS = [
    ("MA", "Madre"),
    ("PA", "Padre"),
    ("HI", "Hijo/a"),
    ("CO", "Cónyuge / Pareja"),
    ("AB", "Abuelo/a"),
    ("HE", "Hermano/a"),
    ("TI", "Tío/a"),
    ("NI", "Nieto/a"),
    ("OT", "Otro"),
]

# ─────────────────────────────────────────────────────────────────────────────
# VALIDACIONES
# ─────────────────────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _validar_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))

def _validar_password(pw: str) -> tuple[bool, str]:
    if len(pw) < 8:
        return False, "Mínimo 8 caracteres."
    if not any(c.isupper() for c in pw):
        return False, "Debe incluir al menos una mayúscula."
    if not any(c.isdigit() for c in pw):
        return False, "Debe incluir al menos un número."
    return True, ""

# ─────────────────────────────────────────────────────────────────────────────
# LEER CREDENCIALES (env vars o interactivo)
# ─────────────────────────────────────────────────────────────────────────────
def _leer_credenciales() -> dict:
    print("\n  📋 CONFIGURACIÓN DEL ADMINISTRADOR INICIAL")
    print("  " + "─" * 50)
    print("  (Podés definir ADMIN_EMAIL y ADMIN_PASSWORD como")
    print("   variables de entorno para saltear este paso)\n")

    # Email
    email = os.environ.get("ADMIN_EMAIL", "").strip()
    if email:
        print(f"  Email:      {email}  (desde ADMIN_EMAIL)")
    else:
        while True:
            email = input("  Email admin: ").strip()
            if _validar_email(email):
                break
            print("  ❌ Email inválido. Intentá de nuevo.")

    # Contraseña
    password = os.environ.get("ADMIN_PASSWORD", "").strip()
    if password:
        print(f"  Contraseña: {'*' * len(password)}  (desde ADMIN_PASSWORD)")
        ok, msg = _validar_password(password)
        if not ok:
            print(f"  ⚠️  La contraseña definida en ADMIN_PASSWORD no cumple los requisitos: {msg}")
            print("     Continuando de todas formas (es tu responsabilidad en producción).")
    else:
        while True:
            password = getpass.getpass("  Contraseña (mín. 8 chars, 1 mayúscula, 1 número): ")
            ok, msg = _validar_password(password)
            if not ok:
                print(f"  ❌ {msg}")
                continue
            confirm = getpass.getpass("  Confirmá la contraseña: ")
            if password != confirm:
                print("  ❌ Las contraseñas no coinciden.")
                continue
            break

    # Nombre y apellido
    nombre   = os.environ.get("ADMIN_NOMBRE",   "Admin").strip()
    apellido = os.environ.get("ADMIN_APELLIDO", "Sistema").strip()

    if not os.environ.get("ADMIN_NOMBRE"):
        nombre_input = input(f"  Nombre [{nombre}]: ").strip()
        if nombre_input:
            nombre = nombre_input

    if not os.environ.get("ADMIN_APELLIDO"):
        apellido_input = input(f"  Apellido [{apellido}]: ").strip()
        if apellido_input:
            apellido = apellido_input

    return {"email": email, "password": password, "nombre": nombre, "apellido": apellido}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
async def init_prod():
    sep = "═" * 58
    print(f"\n{sep}")
    print("  🚀  Acompañarte — Inicialización de producción")
    print(sep)

    # ── 1. Crear tablas ───────────────────────────────────────────────────
    print("\n🔧 Creando estructura de la base de datos…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   ✓ Tablas verificadas / creadas")

    async with AsyncSessionLocal() as db:

        # ── 2. Roles ──────────────────────────────────────────────────────
        print("\n🔧 Verificando roles del sistema…")
        roles_creados = 0
        for r in ROLES:
            existe = await db.execute(select(Rol).where(Rol.key == r["key"]))
            if not existe.scalar_one_or_none():
                db.add(Rol(
                    key=r["key"],
                    label=r["label"],
                    default_path=r["default_path"],
                    nav_config=r["nav_config"],
                ))
                roles_creados += 1
        await db.commit()
        if roles_creados:
            print(f"   ✓ {roles_creados} roles creados")
        else:
            print("   ✓ Roles ya existentes — sin cambios")

        # ── 3. Parentescos ─────────────────────────────────────────────────
        print("\n🔧 Verificando catálogo de parentescos…")
        paren_creados = 0
        for id_p, nombre in PARENTESCOS:
            existe = await db.execute(
                select(Parentesco).where(Parentesco.id_parentesco == id_p)
            )
            if not existe.scalar_one_or_none():
                db.add(Parentesco(id_parentesco=id_p, nombre=nombre))
                paren_creados += 1
        await db.commit()
        if paren_creados:
            print(f"   ✓ {paren_creados} parentescos creados")
        else:
            print("   ✓ Catálogo ya existente — sin cambios")

        # ── 4. Verificar si ya hay un admin ────────────────────────────────
        print("\n🔧 Verificando usuario administrador…")
        rol_admin = (await db.execute(select(Rol).where(Rol.key == "admin"))).scalar_one()

        admin_existente = await db.execute(
            select(Usuario).where(Usuario.rol_id == rol_admin.id)
        )
        if admin_existente.scalar_one_or_none():
            print("   ✓ Ya existe al menos un administrador — sin cambios")
            print(f"\n{sep}")
            print("  ✅  Sistema ya inicializado. Podés ingresar con tu cuenta admin.")
            print(f"{sep}\n")
            return

        # ── 5. Crear primer administrador ──────────────────────────────────
        creds = _leer_credenciales()

        # Verificar email único
        email_dup = await db.execute(
            select(Usuario).where(Usuario.email == creds["email"])
        )
        if email_dup.scalar_one_or_none():
            print(f"\n  ❌ Ya existe un usuario con el email '{creds['email']}'.")
            print("     Usá otro email o iniciá sesión con ese usuario.")
            return

        print("\n  Creando usuario administrador…")
        iniciales = (creds["nombre"][:1] + creds["apellido"][:1]).upper()
        admin_u = Usuario(
            email=creds["email"],
            password_hash=_pwd.hash(creds["password"]),
            nombre=creds["nombre"],
            apellido=creds["apellido"],
            rol_id=rol_admin.id,
            avatar_initials=iniciales,
            avatar_class="av-rd",
            profile_label="Administrador del sistema",
            activo=True,
            email_verificado=True,
        )
        db.add(admin_u)
        await db.flush()

        db.add(Administrador(
            usuario_id=admin_u.id,
            nivel_acceso=3,
            activo=True,
        ))
        await db.commit()

    # ── Resumen ───────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  ✅  SISTEMA INICIALIZADO CORRECTAMENTE")
    print(sep)
    print()
    print("  ACCESO AL SISTEMA")
    print("  " + "─" * 50)
    print(f"  Email:      {creds['email']}")
    print(f"  Contraseña: {'(la que ingresaste)'}")
    print(f"  Rol:        Administrador (nivel 3 — acceso total)")
    print()
    print("  PRÓXIMOS PASOS")
    print("  1. Iniciá sesión con las credenciales de arriba")
    print("  2. Creá los terapeutas desde Admin → Terapeutas")
    print("  3. Cada terapeuta puede registrar sus pacientes")
    print("  4. El familiar recibe sus credenciales por email")
    print(f"\n{sep}\n")


if __name__ == "__main__":
    asyncio.run(init_prod())
