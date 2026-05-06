#!/usr/bin/env bash
# ============================================================
#  verificar_entorno.sh — Acompañarte / VPS Ubuntu (DonWeb)
#
#  Verifica e instala las herramientas necesarias para
#  ejecutar la aplicación en el servidor.
#
#  Uso (como root o con sudo):
#    chmod +x verificar_entorno.sh
#    sudo ./verificar_entorno.sh
# ============================================================

set -euo pipefail

# ── Colores ──────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; WHITE='\033[1;37m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}[OK]${NC} $*"; }
miss() { echo -e "  ${RED}[!!]${NC} $*"; }
info() { echo -e "  ${CYAN}[->]${NC} $*"; }
warn() { echo -e "  ${YELLOW}[~ ]${NC} $*"; }
title(){ echo -e "\n${WHITE}$*${NC}"; }

FALTANTES=()
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Verificar que corre como root ─────────────────────────────
if [[ $EUID -ne 0 ]]; then
    miss "Este script debe ejecutarse como root o con sudo."
    info "Ejecutá: sudo ./verificar_entorno.sh"
    exit 1
fi

# ============================================================
#  CABECERA
# ============================================================
clear
echo ""
echo -e "  ${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${CYAN}║    Acompañarte — Verificación del entorno VPS    ║${NC}"
echo -e "  ${CYAN}║              Ubuntu · DonWeb Cloud               ║${NC}"
echo -e "  ${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================
#  1. ACTUALIZAR PAQUETES DEL SISTEMA
# ============================================================
title "1. Paquetes del sistema"
info "Actualizando lista de paquetes (apt update)..."
apt-get update -qq
ok "Lista de paquetes actualizada."

# ============================================================
#  2. DOCKER Y DOCKER COMPOSE
# ============================================================
title "2. Docker y Docker Compose"

if command -v docker &>/dev/null; then
    DOCKER_VER=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    ok "Docker instalado (v${DOCKER_VER})."
else
    miss "Docker NO está instalado."
    FALTANTES+=("Docker")
    info "Instalando Docker..."
    apt-get install -y ca-certificates curl gnupg lsb-release -qq
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) \
signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -qq
    apt-get install -y docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin -qq
    systemctl enable docker --now
    DOCKER_VER=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    ok "Docker instalado y habilitado (v${DOCKER_VER})."
    FALTANTES=("${FALTANTES[@]/Docker/}")
fi

# Docker Compose (plugin v2)
if docker compose version &>/dev/null; then
    COMPOSE_VER=$(docker compose version --short 2>/dev/null || echo "?")
    ok "Docker Compose (plugin) disponible (v${COMPOSE_VER})."
else
    miss "Docker Compose plugin NO está disponible."
    FALTANTES+=("Docker Compose plugin")
    info "Instalando docker-compose-plugin..."
    apt-get install -y docker-compose-plugin -qq
    ok "Docker Compose plugin instalado."
    FALTANTES=("${FALTANTES[@]/Docker Compose plugin/}")
fi

# Verificar que el daemon esté corriendo
if systemctl is-active --quiet docker; then
    ok "Servicio Docker está activo."
else
    warn "El servicio Docker no está activo. Iniciando..."
    systemctl start docker
    systemctl is-active --quiet docker && ok "Docker iniciado." || {
        miss "No se pudo iniciar Docker."
        FALTANTES+=("Servicio Docker no activo")
    }
fi

# ============================================================
#  3. OLLAMA  (motor de IA — corre en el host, no en Docker)
# ============================================================
title "3. Ollama (motor de IA local)"

if command -v ollama &>/dev/null; then
    OLLAMA_VER=$(ollama --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' || echo "?")
    ok "Ollama instalado (v${OLLAMA_VER})."
else
    miss "Ollama NO está instalado."
    FALTANTES+=("Ollama")
    info "Instalando Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    ok "Ollama instalado."
    FALTANTES=("${FALTANTES[@]/Ollama/}")
fi

# Verificar / iniciar servicio ollama
if systemctl is-active --quiet ollama 2>/dev/null; then
    ok "Servicio Ollama está activo."
elif systemctl list-unit-files --quiet ollama.service &>/dev/null; then
    warn "Servicio Ollama no está activo. Iniciando..."
    systemctl enable ollama --now
    sleep 3
    systemctl is-active --quiet ollama && ok "Ollama iniciado." || {
        miss "No se pudo iniciar el servicio Ollama."
        FALTANTES+=("Servicio Ollama no activo")
    }
else
    # Sin systemd unit — iniciar como proceso en background
    warn "No hay unidad systemd para Ollama. Iniciando en background..."
    nohup ollama serve &>/var/log/ollama.log &
    sleep 4
    if curl -s http://localhost:11434 &>/dev/null; then
        ok "Ollama corriendo en puerto 11434."
    else
        miss "Ollama no responde en el puerto 11434."
        FALTANTES+=("Servidor Ollama no responde")
    fi
fi

# Verificar conectividad en puerto 11434
sleep 2
if curl -s http://localhost:11434 &>/dev/null; then
    ok "Ollama responde en http://localhost:11434."
else
    warn "Ollama no responde todavía en el puerto 11434."
    FALTANTES+=("Ollama no responde en puerto 11434")
fi

# ============================================================
#  4. MODELO DE IA  (qwen2.5:3b)
# ============================================================
title "4. Modelo de IA"

# Leer modelo configurado en .env si existe
MODELO="qwen2.5:3b"
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    MODELO_ENV=$(grep -oP '^OLLAMA_MODEL=\K.*' "$SCRIPT_DIR/.env" | tr -d '[:space:]' || true)
    [[ -n "$MODELO_ENV" ]] && MODELO="$MODELO_ENV"
fi
info "Modelo configurado: $MODELO"

if ollama list 2>/dev/null | grep -q "${MODELO%%:*}"; then
    ok "Modelo '$MODELO' ya está descargado."
else
    miss "Modelo '$MODELO' NO está descargado."
    FALTANTES+=("Modelo Ollama '$MODELO'")
    info "Descargando modelo '$MODELO' (esto puede tardar varios minutos)..."
    if ollama pull "$MODELO"; then
        ok "Modelo '$MODELO' descargado correctamente."
        FALTANTES=("${FALTANTES[@]/Modelo Ollama \'$MODELO\'/}")
    else
        miss "Error al descargar el modelo '$MODELO'."
        info "Podés descargarlo manualmente con: ollama pull $MODELO"
    fi
fi

# ============================================================
#  5. ARCHIVO .env
# ============================================================
title "5. Archivo de configuración (.env)"

ENV_PATH="$SCRIPT_DIR/.env"
EXAMPLE_PATH="$SCRIPT_DIR/.env.example"

if [[ -f "$ENV_PATH" ]]; then
    ok "Archivo .env encontrado."

    # Advertir si todavía tiene claves de ejemplo
    if grep -qE "^(SECRET_KEY|ENCRYPTION_KEY)=cambia_esto|genera_una_clave" "$ENV_PATH"; then
        warn "El .env tiene claves de ejemplo sin cambiar (SECRET_KEY / ENCRYPTION_KEY)."
        warn "Generá claves seguras antes de exponer la aplicación a Internet:"
        echo ""
        echo -e "  ${YELLOW}SECRET_KEY:${NC}"
        echo "    python3 -c \"import secrets; print(secrets.token_hex(32))\""
        echo -e "  ${YELLOW}ENCRYPTION_KEY:${NC}"
        echo "    python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        echo ""
        FALTANTES+=("Claves de seguridad sin configurar en .env")
    fi
else
    miss "No existe el archivo .env."
    if [[ -f "$EXAMPLE_PATH" ]]; then
        info "Creando .env desde .env.example..."
        cp "$EXAMPLE_PATH" "$ENV_PATH"
        ok "Archivo .env creado."
        warn "IMPORTANTE: editá el .env y configurá SECRET_KEY y ENCRYPTION_KEY con valores seguros."
        FALTANTES+=("Claves de seguridad sin configurar en .env")
    else
        miss "Tampoco existe .env.example. Creá el .env manualmente."
        FALTANTES+=("Archivo .env")
    fi
fi

# ============================================================
#  6. PUERTOS NECESARIOS
# ============================================================
title "6. Puertos del firewall (UFW)"

if command -v ufw &>/dev/null && ufw status | grep -q "Status: active"; then
    for PUERTO in 80 443 8000 5173; do
        if ufw status | grep -qE "^$PUERTO"; then
            ok "Puerto $PUERTO abierto."
        else
            warn "Puerto $PUERTO no está abierto en UFW."
            info "Abriendo puerto $PUERTO..."
            ufw allow "$PUERTO"/tcp
            ok "Puerto $PUERTO habilitado."
        fi
    done
else
    ok "UFW no está activo — no se requiere configuración de firewall adicional."
fi

# ============================================================
#  RESUMEN FINAL
# ============================================================
echo ""
echo -e "  ${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "  ${WHITE}RESUMEN${NC}"
echo -e "  ${CYAN}══════════════════════════════════════════════════${NC}"
echo ""

# Filtrar entradas vacías del array
FALTANTES_LIMPIOS=()
for item in "${FALTANTES[@]}"; do
    [[ -n "$item" ]] && FALTANTES_LIMPIOS+=("$item")
done

if [[ ${#FALTANTES_LIMPIOS[@]} -eq 0 ]]; then
    ok "Entorno completo. El servidor está listo para iniciar Acompañarte."
    echo ""
    echo -e "  ${WHITE}Para iniciar la aplicación ejecutá:${NC}"
    echo -e "    ${YELLOW}cd $(pwd)${NC}"
    echo -e "    ${YELLOW}docker compose up -d --build${NC}"
    echo ""
    # Obtener IP pública del servidor
    IP_PUBLICA=$(curl -s ifconfig.me 2>/dev/null || curl -s api.ipify.org 2>/dev/null || echo "IP_DEL_SERVIDOR")
    echo -e "  ${WHITE}Luego accedé desde el navegador:${NC}"
    echo -e "    ${YELLOW}http://${IP_PUBLICA}        (Aplicación)${NC}"
    echo -e "    ${YELLOW}http://${IP_PUBLICA}:5050   (pgAdmin)${NC}"
    echo ""
else
    miss "Hay ${#FALTANTES_LIMPIOS[@]} elemento(s) pendiente(s):"
    for f in "${FALTANTES_LIMPIOS[@]}"; do
        echo -e "    ${RED}•${NC} $f"
    done
    echo ""
    info "Resolvé los puntos pendientes y volvé a ejecutar este script."
    echo ""
fi
