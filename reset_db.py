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
  auditoria          consentimientos     alertas
  mensajes_ia        sesiones_ia         progreso_actividad
  actividades_familiar                   permisos_seguimiento
  registros_seguimiento                  miembros_equipo
  equipos_terapeuticos                   vinculos_paciente
  contactos_publicos                     pacientes

DETECCIÓN DE ENTORNO
────────────────────
  El script detecta automáticamente el entorno según los archivos
  presentes en la raíz del proyecto:

    Desarrollo  →  .env  +  docker-compose.yml       (puerto 5432 expuesto)
    Producción  →  .env.prod  +  docker-compose.prod.yml  (puerto NO expuesto)

  En producción el puerto 5432 no está expuesto al host. El script
  conecta directamente dentro del contenedor Docker usando docker exec.

USO
────
  # Detección automática de entorno (recomendado):
  python reset_db.py

  # Forzar entorno explícitamente:
  python reset_db.py --env dev
  python reset_db.py --env prod

  # Sobrescribir credenciales (cualquier entorno):
  python reset_db.py --host localhost --port 5432 \\
                     --user acomp_user --password TU_PASSWORD \\
                     --dbname acompanarte_db

  # Sin confirmación interactiva (CI / automatización):
  python reset_db.py --yes
"""

import argparse
import os
import re
import sys
import subprocess
import importlib

# ─────────────────────────────────────────────────────────────────────────────
# VERIFICACIÓN Y AUTO-INSTALACIÓN DE DEPENDENCIAS
# Se ejecuta antes de cualquier otra cosa, usando solo stdlib.
# ─────────────────────────────────────────────────────────────────────────────

_PYTHON_MIN   = (3, 8)
_DEPENDENCIAS = [
    ("psycopg2", "psycopg2-binary"),
]


def _verificar_python() -> None:
    if sys.version_info[:2] < _PYTHON_MIN:
        print(f"❌  Python {_PYTHON_MIN[0]}.{_PYTHON_MIN[1]} o superior es requerido.")
        print(f"    Versión actual: {sys.version.split()[0]}")
        print("    Descargá la última versión en: https://www.python.org/downloads/")
        sys.exit(1)


def _instalar_modulo(paquete_pip: str) -> bool:
    for cmd in [
        [sys.executable, "-m", "pip", "install", paquete_pip],
        [sys.executable, "-m", "pip", "install", "--break-system-packages", paquete_pip],
        [sys.executable, "-m", "pip", "install", "--user", paquete_pip],
    ]:
        try:
            if subprocess.run(cmd, capture_output=True).returncode == 0:
                return True
        except Exception:
            continue
    return False


def _verificar_dependencias() -> None:
    print("\n🔍  Verificando dependencias…\n")
    faltantes = []
    for nombre_import, paquete_pip in _DEPENDENCIAS:
        try:
            importlib.import_module(nombre_import)
            print(f"  ✓  {nombre_import:<20} — encontrado")
        except ImportError:
            print(f"  ✗  {nombre_import:<20} — no encontrado")
            faltantes.append((nombre_import, paquete_pip))

    if not faltantes:
        print("\n  Todas las dependencias están disponibles.")
        return

    print()
    errores = []
    for nombre_import, paquete_pip in faltantes:
        print(f"  ⚠️   No se encuentra '{nombre_import}'.")
        print(f"       Se está instalando '{paquete_pip}', aguarde…")
        if _instalar_modulo(paquete_pip):
            try:
                importlib.import_module(nombre_import)
                print(f"  ✓   '{paquete_pip}' instalado correctamente.\n")
            except ImportError:
                print(f"  ✗   '{paquete_pip}' se instaló pero no se pudo importar.\n")
                errores.append(nombre_import)
        else:
            print(f"  ✗   No se pudo instalar '{paquete_pip}'.")
            print(f"       Intentá manualmente:  pip install {paquete_pip}\n")
            errores.append(nombre_import)

    if errores:
        print("❌  No se pudieron instalar las siguientes dependencias:")
        for m in errores:
            print(f"    • {m}")
        print("\nInstalá los módulos faltantes manualmente y volvé a ejecutar el script.")
        sys.exit(1)


_verificar_python()
_verificar_dependencias()

import psycopg2           # noqa: E402
from psycopg2 import sql  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# TABLAS
# ─────────────────────────────────────────────────────────────────────────────

TABLAS_A_BORRAR = [
    # 1. Auditoría e historial
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
    # 7. Núcleo clínico
    "pacientes",
]

TABLAS_CONSERVADAS = [
    "roles", "parentescos", "reglas_ia",
    "provincias", "localidades", "diagnosticos",
    "recursos_profesionales",
    "usuarios", "administradores", "terapeutas", "familiares",
]


# ─────────────────────────────────────────────────────────────────────────────
# DETECCIÓN DE ENTORNO
# ─────────────────────────────────────────────────────────────────────────────

# Directorio donde está este script (raíz del proyecto)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_ENTORNOS = {
    "prod": {
        "env_file":     ".env.prod",
        "compose_file": "docker-compose.prod.yml",
        "label":        "Producción",
        "puerto_expuesto": False,          # el puerto 5432 NO se expone al host
        "contenedor_db": "acompanarte_db", # nombre del contenedor PostgreSQL
    },
    "dev": {
        "env_file":     ".env",
        "compose_file": "docker-compose.yml",
        "label":        "Desarrollo",
        "puerto_expuesto": True,           # el puerto 5432 SÍ se expone al host
        "contenedor_db": "acompanarte_db",
    },
}


def _detectar_entorno() -> str:
    """
    Determina el entorno según los archivos presentes en la raíz del proyecto.
    Prioridad: si existe .env.prod  → producción; si solo existe .env → desarrollo.
    """
    tiene_prod = os.path.isfile(os.path.join(_BASE_DIR, ".env.prod"))
    tiene_dev  = os.path.isfile(os.path.join(_BASE_DIR, ".env"))

    if tiene_prod:
        return "prod"
    if tiene_dev:
        return "dev"
    return "dev"   # fallback: intentar con defaults de desarrollo


def _leer_env_file(env_key: str) -> dict:
    """
    Lee el archivo .env correspondiente al entorno y retorna un dict con
    las variables DB_USER, DB_PASSWORD, DB_NAME y DATABASE_URL (si existe).
    Ignora líneas en blanco y comentarios.
    """
    env_file = os.path.join(_BASE_DIR, _ENTORNOS[env_key]["env_file"])
    vars_env = {}

    if not os.path.isfile(env_file):
        return vars_env

    with open(env_file, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if "=" in linea:
                clave, _, valor = linea.partition("=")
                clave  = clave.strip()
                valor  = valor.strip().strip('"').strip("'")
                vars_env[clave] = valor

    return vars_env


def _mostrar_entorno(env_key: str, env_file: str) -> None:
    cfg = _ENTORNOS[env_key]
    print(f"\n  Entorno detectado : {cfg['label']}")
    print(f"  Archivo de config  : {env_file}")
    print(f"  Docker Compose     : {cfg['compose_file']}")
    if not cfg["puerto_expuesto"]:
        print("  Acceso a BD        : via docker exec (puerto no expuesto al host)")
    else:
        print("  Acceso a BD        : localhost (puerto 5432 expuesto al host)")


# ─────────────────────────────────────────────────────────────────────────────
# CONEXIÓN
# ─────────────────────────────────────────────────────────────────────────────

def _conectar(args, env_key: str, vars_env: dict) -> psycopg2.extensions.connection:
    """
    Estrategia de conexión:
      - Si se pasaron flags de CLI  → usarlos directamente.
      - Si el entorno es dev        → localhost con credenciales del .env.
      - Si el entorno es prod       → el puerto no está expuesto; se lanza
                                      error descriptivo con instrucciones.
    """
    # 1. Flags de CLI tienen prioridad absoluta
    if args.host:
        return psycopg2.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            dbname=args.dbname,
        )

    # 2. Credenciales del archivo .env detectado
    user     = vars_env.get("DB_USER",     "acomp_user")
    password = vars_env.get("DB_PASSWORD", "")
    dbname   = vars_env.get("DB_NAME",     "acompanarte_db")

    # 3. En producción el puerto 5432 no está expuesto → usar docker exec
    if env_key == "prod" and not args.host:
        return _conectar_via_docker(vars_env, _ENTORNOS["prod"]["contenedor_db"])

    # 4. Desarrollo: conexión directa a localhost
    return psycopg2.connect(
        host="localhost",
        port=5432,
        user=user,
        password=password,
        dbname=dbname,
    )


def _conectar_via_docker(vars_env: dict, contenedor: str) -> psycopg2.extensions.connection:
    """
    En producción el puerto 5432 no está expuesto al host.
    Se verifica que Docker esté disponible y que el contenedor esté corriendo,
    luego se conecta al puerto interno mapeando temporalmente a través de
    'docker exec' para ejecutar los comandos SQL directamente.

    Como psycopg2 necesita un socket TCP real, intentamos un túnel temporal
    o informamos al usuario cómo proceder.
    """
    # Verificar que docker esté disponible
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        _error_produccion_sin_docker(contenedor, vars_env)

    # Verificar que el contenedor de la BD esté corriendo
    resultado = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Running}}", contenedor],
        capture_output=True, text=True,
    )
    if resultado.returncode != 0 or resultado.stdout.strip() != "true":
        print(f"\n❌  El contenedor '{contenedor}' no está corriendo.")
        print(f"    Levantalo con:  docker compose -f docker-compose.prod.yml up -d db")
        sys.exit(1)

    # En producción conectamos mapeando el puerto interno vía docker exec
    # psycopg2 no puede usar docker exec directamente, así que levantamos
    # un túnel local efímero con socat dentro del contenedor si está disponible,
    # o informamos al usuario que exponga el puerto temporalmente.
    print("\n  ℹ️   Entorno de producción: el puerto 5432 no está expuesto al host.")
    print("       Intentando conexión directa dentro de la red Docker…")

    # Obtener la IP interna del contenedor de BD
    ip_result = subprocess.run(
        ["docker", "inspect", "--format",
         "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", contenedor],
        capture_output=True, text=True,
    )
    ip_contenedor = ip_result.stdout.strip()

    if not ip_contenedor:
        _error_produccion_sin_docker(contenedor, vars_env)

    user     = vars_env.get("DB_USER",     "acomp_user")
    password = vars_env.get("DB_PASSWORD", "")
    dbname   = vars_env.get("DB_NAME",     "acompanarte_db")

    try:
        conn = psycopg2.connect(
            host=ip_contenedor,
            port=5432,
            user=user,
            password=password,
            dbname=dbname,
        )
        print(f"  ✓   Conectado al contenedor en {ip_contenedor}:5432")
        return conn
    except psycopg2.OperationalError:
        _error_produccion_sin_docker(contenedor, vars_env)


def _error_produccion_sin_docker(contenedor: str, vars_env: dict) -> None:
    """Muestra instrucciones detalladas cuando no se puede conectar en prod."""
    user   = vars_env.get("DB_USER",   "DB_USER")
    dbname = vars_env.get("DB_NAME",   "DB_NAME")
    print()
    print("❌  No se pudo conectar a la base de datos en producción.")
    print()
    print("    El puerto 5432 no está expuesto al host en docker-compose.prod.yml.")
    print("    Tenés dos opciones:\n")
    print("    Opción A — Exponer el puerto temporalmente:")
    print(f"      1. En docker-compose.prod.yml, bajo el servicio 'db', agregá:")
    print( "            ports:")
    print( "              - \"5432:5432\"")
    print( "      2. Reiniciá el contenedor:")
    print(f"            docker compose -f docker-compose.prod.yml up -d db")
    print( "      3. Corré el script y luego remové el puerto del compose.")
    print()
    print("    Opción B — Pasar las credenciales y conectar al contenedor:")
    print(f"      python reset_db.py --env prod \\")
    print(f"        --host <IP_SERVIDOR> --port 5432 \\")
    print(f"        --user {user} --password TU_PASSWORD \\")
    print(f"        --dbname {dbname}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE VISUALIZACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def _contar_filas(cur, tabla: str) -> int:
    cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(tabla)))
    return cur.fetchone()[0]


def _mostrar_resumen(cur) -> int:
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
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Inicializa la BD de Acompañarte para primer uso real.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--env", choices=["dev", "prod"], default=None,
        help="Forzar entorno: dev (usa .env) o prod (usa .env.prod). "
             "Por defecto se detecta automáticamente.",
    )
    parser.add_argument("--host",     default=None, help="Host PostgreSQL")
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

    # ── Detectar entorno ──────────────────────────────────────────────────────
    env_key  = args.env if args.env else _detectar_entorno()
    cfg      = _ENTORNOS[env_key]
    vars_env = _leer_env_file(env_key)

    # Si se pasaron credenciales por CLI, sobreescribir las del .env
    if args.user:
        vars_env["DB_USER"] = args.user
    if args.password:
        vars_env["DB_PASSWORD"] = args.password
    if args.dbname:
        vars_env["DB_NAME"] = args.dbname

    _mostrar_entorno(env_key, cfg["env_file"])

    if not vars_env:
        print(f"\n  ⚠️   No se encontró el archivo '{cfg['env_file']}'.")
        print("       Se usarán los valores por defecto del docker-compose.")

    # ── Conectar ──────────────────────────────────────────────────────────────
    print("\n🔌  Conectando a la base de datos…")
    try:
        conn = _conectar(args, env_key, vars_env)
    except psycopg2.OperationalError as e:
        print(f"\n❌  No se pudo conectar:\n    {e}")
        print()
        print("Verificá que:")
        if env_key == "dev":
            print("  • Docker está corriendo  →  docker compose up -d db")
            print("  • El puerto 5432 está mapeado en docker-compose.yml")
        else:
            print("  • El contenedor de BD está corriendo  →  docker compose -f docker-compose.prod.yml up -d db")
        print(f"  • Las credenciales en '{cfg['env_file']}' son correctas")
        sys.exit(1)

    print(f"  ✓   Conexión establecida.")

    conn.autocommit = False
    cur = conn.cursor()

    # ── Resumen previo ────────────────────────────────────────────────────────
    print("\n📊  Estado actual de las tablas:")
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
            cur.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(tabla)))
            n = cur.rowcount
            print(f"  ✓  {tabla:<32} — {n} fila(s) eliminada(s)")
        except psycopg2.Error as e:
            print(f"  ✗  {tabla:<32} — ERROR: {e.pgerror or e}")
            errores.append(tabla)
            conn.rollback()
            cur = conn.cursor()

    if errores:
        print()
        print(f"⚠️   Hubo errores en {len(errores)} tabla(s): {errores}")
        print("    Realizando ROLLBACK — ningún cambio fue guardado.")
        conn.rollback()
        cur.close()
        conn.close()
        sys.exit(1)

    # ── Commit ────────────────────────────────────────────────────────────────
    conn.commit()
    print()
    print("✅  Commit realizado correctamente.")

    # ── Resumen final ─────────────────────────────────────────────────────────
    print("\n📊  Estado final de las tablas:")
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
