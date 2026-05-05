#!/usr/bin/env python3
"""
reset_db.py — Inicialización de la base de datos para primer uso
================================================================
Borra todos los datos transaccionales (pacientes, registros, sesiones IA,
alertas, etc.) y deja intactos:

  ✅ CONSERVADOS
  ─────────────────────────────────────────────────────────────
  roles              → configuración de roles y nav del sidebar
  parentescos        → catálogo MA/PA/AB/TI/HE/TU/OT
  reglas_ia          → reglas de comportamiento del asistente IA
  provincias         → catálogo geográfico argentino
  localidades        → catálogo geográfico argentino
  diagnosticos       → catálogo CIE-11 / DSM-5
  recursos_profes.   → bibliografía RAG validada (embeddings incluidos)
  usuarios           → cuentas de acceso al sistema
  administradores    → perfil de administrador
  terapeutas         → perfil de terapeuta
  familiares         → perfil de familiar

  🗑️  BORRADAS (datos transaccionales / demo)
  ─────────────────────────────────────────────────────────────
  auditoria
  consentimientos
  alertas
  mensajes_ia
  sesiones_ia
  progreso_actividad
  actividades_familiar
  permisos_seguimiento
  registros_seguimiento
  miembros_equipo
  equipos_terapeuticos
  vinculos_paciente
  contactos_publicos
  pacientes

USO
────
  # Desde la raíz del proyecto (con Docker corriendo):
  python reset_db.py

  # Pasando credenciales explícitas:
  python reset_db.py --host localhost --port 5432 \\
                     --user acomp_user --password TU_PASSWORD \\
                     --dbname acompanarte_db

  # Ejecución sin confirmación interactiva (CI / automatización):
  python reset_db.py --yes
"""

import argparse
import os
import sys

# ── Dependencia: psycopg2 ─────────────────────────────────────────────────────
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌  psycopg2 no está instalado.")
    print("    Instalalo con:  pip install psycopg2-binary")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Tablas a borrar — ORDEN RESPETA DEPENDENCIAS FK
# (las que tienen FK hacia otras van primero)
# ─────────────────────────────────────────────────────────────────────────────
TABLAS_A_BORRAR = [
    # 1. Auditoría e historial inmutables
    "auditoria",
    "consentimientos",
    # 2. Módulo IA
    "alertas",
    "mensajes_ia",
    "sesiones_ia",
    # 3. Actividades
    "progreso_actividad",
    "actividades_familiar",
    # 4. Seguimientos
    "permisos_seguimiento",
    "registros_seguimiento",
    # 5. Equipos
    "miembros_equipo",
    "equipos_terapeuticos",
    # 6. Vínculos y contactos
    "vinculos_paciente",
    "contactos_publicos",
    # 7. Núcleo clínico (al final porque el resto lo referencia)
    "pacientes",
]

# Tablas que NO se tocan (documentadas para transparencia)
TABLAS_CONSERVADAS = [
    "roles",
    "parentescos",
    "reglas_ia",
    "provincias",
    "localidades",
    "diagnosticos",
    "recursos_profesionales",
    "usuarios",
    "administradores",
    "terapeutas",
    "familiares",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_db_url(url: str) -> dict:
    """
    Extrae host/port/user/password/dbname de una DATABASE_URL.
    Soporta postgresql+asyncpg:// y postgresql://.
    """
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    # psycopg2 puede parsear la URL directamente
    return {"dsn": url.replace("postgresql://", "postgresql://")}


def _conectar(args) -> psycopg2.extensions.connection:
    """Abre conexión a PostgreSQL usando args de CLI o variables de entorno."""

    # 1. Prioridad: flags de CLI
    if args.host:
        conn = psycopg2.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            dbname=args.dbname,
        )
        return conn

    # 2. Variable DATABASE_URL (quitando el driver asyncpg)
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        db_url_pg = db_url.replace("postgresql+asyncpg://", "postgresql://")
        # Si apunta a 'db' (hostname Docker), reemplazar por localhost
        db_url_pg = db_url_pg.replace("@db:", "@localhost:")
        try:
            conn = psycopg2.connect(dsn=db_url_pg)
            return conn
        except Exception as e:
            print(f"⚠️  No se pudo conectar con DATABASE_URL: {e}")

    # 3. Valores por defecto del docker-compose
    conn = psycopg2.connect(
        host=args.host or "localhost",
        port=args.port or 5432,
        user=args.user or os.getenv("DB_USER", "acomp_user"),
        password=args.password or os.getenv("DB_PASSWORD", "acomp_pass"),
        dbname=args.dbname or os.getenv("DB_NAME", "acompanarte_db"),
    )
    return conn


def _contar_filas(cur, tabla: str) -> int:
    cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(tabla)))
    return cur.fetchone()[0]


def _mostrar_resumen(cur):
    """Muestra cuántas filas hay en cada tabla antes de borrar."""
    ancho = 32
    print()
    print("┌" + "─" * (ancho + 2) + "┬" + "─" * 12 + "┐")
    print(f"│ {'Tabla':<{ancho}} │ {'Filas':>10} │")
    print("├" + "─" * (ancho + 2) + "┼" + "─" * 12 + "┤")

    total_borrar = 0
    for tabla in TABLAS_A_BORRAR:
        try:
            n = _contar_filas(cur, tabla)
        except Exception:
            n = "?"
        total_borrar += (n if isinstance(n, int) else 0)
        marca = "🗑️ " if (isinstance(n, int) and n > 0) else "   "
        print(f"│ {marca}{tabla:<{ancho - 3}} │ {str(n):>10} │")

    print("├" + "─" * (ancho + 2) + "┼" + "─" * 12 + "┤")

    print(f"│ {'  ── CONSERVADAS ──':<{ancho + 1}} │ {'':>10} │")
    print("├" + "─" * (ancho + 2) + "┼" + "─" * 12 + "┤")
    for tabla in TABLAS_CONSERVADAS:
        try:
            n = _contar_filas(cur, tabla)
        except Exception:
            n = "?"
        print(f"│   {'✅ ' + tabla:<{ancho - 2}} │ {str(n):>10} │")

    print("└" + "─" * (ancho + 2) + "┴" + "─" * 12 + "┘")
    print()
    return total_borrar


# ─────────────────────────────────────────────────────────────────────────────
# Lógica principal
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Inicializa la BD de Acompañarte para primer uso real.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--host",     default=None, help="Host PostgreSQL (default: localhost)")
    parser.add_argument("--port",     default=5432, type=int, help="Puerto (default: 5432)")
    parser.add_argument("--user",     default=None, help="Usuario DB")
    parser.add_argument("--password", default=None, help="Contraseña DB")
    parser.add_argument("--dbname",   default=None, help="Nombre de la base de datos")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Ejecutar sin pedir confirmación interactiva")
    args = parser.parse_args()

    print()
    print("=" * 62)
    print("   Acompañarte — Script de inicialización de base de datos")
    print("=" * 62)

    # ── Conectar ──────────────────────────────────────────────────────────────
    print("\n🔌  Conectando a la base de datos…")
    try:
        conn = _conectar(args)
    except psycopg2.OperationalError as e:
        print(f"\n❌  No se pudo conectar:\n    {e}")
        print()
        print("Asegurate de que:")
        print("  • Docker está corriendo  →  docker compose up -d db")
        print("  • El puerto 5432 está mapeado en docker-compose.yml")
        print("  • Las credenciales coinciden con las del .env")
        sys.exit(1)

    conn.autocommit = False
    cur = conn.cursor()

    # ── Resumen previo ────────────────────────────────────────────────────────
    print("\n📊  Estado actual de las tablas:\n")
    total = _mostrar_resumen(cur)

    if total == 0:
        print("✅  No hay datos transaccionales para borrar. La BD ya está limpia.")
        cur.close()
        conn.close()
        sys.exit(0)

    # ── Confirmación ──────────────────────────────────────────────────────────
    if not args.yes:
        print(f"⚠️   Se borrarán {total} filas de {len(TABLAS_A_BORRAR)} tablas.")
        print("    Los usuarios, recursos RAG, catálogos y roles se CONSERVAN.")
        print()
        respuesta = input("   ¿Confirmar la inicialización? [s/N]: ").strip().lower()
        if respuesta not in ("s", "si", "sí", "y", "yes"):
            print("\n🚫  Operación cancelada.")
            cur.close()
            conn.close()
            sys.exit(0)

    # ── Ejecución ─────────────────────────────────────────────────────────────
    print()
    print("🗑️   Borrando datos transaccionales…")
    print()

    errores = []
    for tabla in TABLAS_A_BORRAR:
        try:
            cur.execute(
                sql.SQL("DELETE FROM {}").format(sql.Identifier(tabla))
            )
            n = cur.rowcount
            estado = f"  ✓  {tabla:<32} — {n} fila(s) eliminada(s)"
            print(estado)
        except psycopg2.Error as e:
            print(f"  ✗  {tabla:<32} — ERROR: {e.pgerror or e}")
            errores.append(tabla)
            conn.rollback()
            # Retomar la transacción para intentar las siguientes tablas
            cur = conn.cursor()

    if errores:
        print()
        print(f"⚠️   Hubo errores en {len(errores)} tabla(s): {errores}")
        print("    Realizando ROLLBACK completo — ningún cambio fue guardado.")
        conn.rollback()
        cur.close()
        conn.close()
        sys.exit(1)

    # ── Commit ────────────────────────────────────────────────────────────────
    conn.commit()
    print()
    print("✅  Commit realizado correctamente.")

    # ── Resumen final ─────────────────────────────────────────────────────────
    print("\n📊  Estado final de las tablas:\n")
    cur = conn.cursor()
    _mostrar_resumen(cur)

    cur.close()
    conn.close()

    print("🎉  Base de datos inicializada para primer uso.")
    print()
    print("Próximos pasos:")
    print("  1. Verificá que los usuarios del sistema pueden ingresar.")
    print("  2. Cargá los recursos RAG (bibliografía) si no están presentes.")
    print("  3. ¡Listo para el primer uso real!")
    print()


if __name__ == "__main__":
    main()
