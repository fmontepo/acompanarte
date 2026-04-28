#!/usr/bin/env bash
# scripts/deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
# Script de despliegue para PRODUCCIÓN de Acompañarte
#
# Uso:
#   bash scripts/deploy.sh            # deploy normal (pull + build + up)
#   bash scripts/deploy.sh --first    # primer despliegue (incluye init BD y seed)
#   bash scripts/deploy.sh --restart  # solo reiniciar servicios sin rebuild
#
# Requisitos previos en el servidor:
#   - Docker y Docker Compose instalados
#   - Ollama instalado y corriendo en el host
#   - Archivo .env.prod creado a partir de .env.prod.example
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colores para output ───────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warning() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

COMPOSE_CMD="docker compose -f docker-compose.prod.yml --env-file .env.prod"

# ── Validaciones previas ──────────────────────────────────────────────────────
info "Verificando requisitos..."

[[ -f ".env.prod" ]] || error ".env.prod no encontrado. Copiá .env.prod.example y completá los valores."

# Verificar que los valores placeholder fueron reemplazados
if grep -q "CAMBIAR_" .env.prod; then
    error "El archivo .env.prod tiene valores sin completar (contiene 'CAMBIAR_'). Editalo antes de desplegar."
fi

command -v docker >/dev/null 2>&1 || error "Docker no está instalado."

# Verificar Ollama
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    warning "Ollama no responde en puerto 11434. El módulo IA no funcionará hasta que esté activo."
    warning "Para iniciar Ollama: sudo systemctl start ollama"
fi

success "Validaciones OK"

# ── Modo --restart ────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--restart" ]]; then
    info "Reiniciando servicios..."
    $COMPOSE_CMD restart
    success "Servicios reiniciados."
    exit 0
fi

# ── Backup de la BD antes de actualizar ──────────────────────────────────────
if $COMPOSE_CMD ps db 2>/dev/null | grep -q "running"; then
    info "Realizando backup de la BD antes de actualizar..."
    bash scripts/backup_db.sh || warning "Backup falló — continuando de todas formas."
fi

# ── Pull del repositorio ──────────────────────────────────────────────────────
info "Actualizando código desde Git..."
git pull origin main || warning "git pull falló — continuando con la versión local."

# ── Build y deploy ────────────────────────────────────────────────────────────
info "Construyendo imágenes Docker..."
$COMPOSE_CMD build --no-cache

info "Levantando servicios en producción..."
$COMPOSE_CMD up -d

# Esperar a que la BD esté lista
info "Esperando que la base de datos esté lista..."
for i in {1..30}; do
    if $COMPOSE_CMD exec -T db pg_isready -U "${DB_USER:-acomp_user}" >/dev/null 2>&1; then
        success "Base de datos lista."
        break
    fi
    sleep 2
done

# ── Primer despliegue: inicializar BD ────────────────────────────────────────
if [[ "${1:-}" == "--first" ]]; then
    info "Primer despliegue — inicializando base de datos..."
    $COMPOSE_CMD exec -T backend python init_prod.py
    success "Base de datos inicializada."

    info "Descargando modelo Ollama (puede tardar varios minutos)..."
    OLLAMA_MODEL=$(grep OLLAMA_MODEL .env.prod | cut -d= -f2)
    ollama pull "${OLLAMA_MODEL:-qwen2.5:3b}"
    success "Modelo IA descargado."
fi

# ── Verificación final ────────────────────────────────────────────────────────
info "Verificando estado de los servicios..."
sleep 5
$COMPOSE_CMD ps

# Health check básico
if curl -sf http://localhost/api/v1/health >/dev/null 2>&1; then
    success "API respondiendo correctamente."
elif curl -sf http://localhost >/dev/null 2>&1; then
    success "Frontend accesible."
else
    warning "No se pudo verificar el health check. Revisá los logs:"
    warning "  $COMPOSE_CMD logs --tail=50"
fi

echo ""
success "═══════════════════════════════════════════"
success " Acompañarte desplegado correctamente ✅"
success "═══════════════════════════════════════════"
echo ""
info "Ver logs en tiempo real:"
echo "  $COMPOSE_CMD logs -f"
info "Detener:"
echo "  $COMPOSE_CMD down"
