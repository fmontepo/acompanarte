#!/usr/bin/env bash
# scripts/backup_db.sh
# ─────────────────────────────────────────────────────────────────────────────
# Backup automático de la base de datos PostgreSQL de producción.
#
# Uso manual:
#   bash scripts/backup_db.sh
#
# Uso automático (crontab -e en el servidor):
#   # Backup diario a las 3:00 AM
#   0 3 * * * cd /opt/acompanarte && bash scripts/backup_db.sh >> /var/log/acompanarte_backup.log 2>&1
#
# Retención: guarda los últimos 7 backups, elimina los más antiguos.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuración ─────────────────────────────────────────────────────────────
BACKUP_DIR="/opt/acompanarte/backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/acompanarte_${TIMESTAMP}.sql.gz"

COMPOSE_CMD="docker compose -f docker-compose.prod.yml --env-file .env.prod"

# ── Crear directorio de backups si no existe ──────────────────────────────────
mkdir -p "${BACKUP_DIR}"

# ── Leer configuración desde .env.prod ───────────────────────────────────────
if [[ -f ".env.prod" ]]; then
    DB_USER_VAL=$(grep "^DB_USER=" .env.prod | cut -d= -f2 | tr -d '"')
    DB_NAME_VAL=$(grep "^DB_NAME=" .env.prod | cut -d= -f2 | tr -d '"')
else
    DB_USER_VAL="${DB_USER:-acomp_user}"
    DB_NAME_VAL="${DB_NAME:-acompanarte_db}"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup de '${DB_NAME_VAL}'..."

# ── Ejecutar pg_dump dentro del contenedor ────────────────────────────────────
$COMPOSE_CMD exec -T db \
    pg_dump -U "${DB_USER_VAL}" "${DB_NAME_VAL}" \
    | gzip > "${BACKUP_FILE}"

BACKUP_SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup guardado: ${BACKUP_FILE} (${BACKUP_SIZE})"

# ── Eliminar backups con más de RETENTION_DAYS días ──────────────────────────
DELETED=$(find "${BACKUP_DIR}" -name "acompanarte_*.sql.gz" \
    -mtime "+${RETENTION_DAYS}" -type f -print -delete | wc -l)

if [[ "${DELETED}" -gt 0 ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Eliminados ${DELETED} backup(s) con más de ${RETENTION_DAYS} días."
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completado exitosamente ✅"
echo ""
echo "Backups disponibles:"
ls -lh "${BACKUP_DIR}"/acompanarte_*.sql.gz 2>/dev/null || echo "  (ninguno)"
