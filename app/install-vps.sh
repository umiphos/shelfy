#!/usr/bin/env bash
set -Eeuo pipefail

# Instalador reproducible para la VPS de PrecioInbox y Turismo.
# Uso:
#   sudo ACME_EMAIL=correo@dominio.com bash scripts/install-vps.sh
#
# Variables opcionales:
#   DEPLOY_OWNER=usuario
#   TURISMO_ADMIN_EMAIL=admin@dominio.com
#   TURISMO_ADMIN_PASSWORD=una-clave-segura
#   SWAP_SIZE_GB=8

readonly PRECIOINBOX_REPO="https://github.com/umiphos/shelfy.git"
readonly TURISMO_REPO="https://github.com/umiphos/wanderly.git"
readonly CADDY_REPO="https://github.com/umiphos/caddy-server-a.git"

readonly CADDY_DIR="/opt/infra/caddy"
readonly PRECIOINBOX_DIR="/opt/apps/precioinbox/backend/shelfy"
readonly TURISMO_DIR="/opt/apps/turismo/backend"
readonly CREDENTIALS_FILE="/root/precioinbox-install-credentials.txt"

ACME_EMAIL="${ACME_EMAIL:-}"
DEPLOY_OWNER="${DEPLOY_OWNER:-${SUDO_USER:-root}}"
DEPLOY_GROUP=""
TURISMO_ADMIN_EMAIL="${TURISMO_ADMIN_EMAIL:-admin@precioinbox.com}"
TURISMO_ADMIN_PASSWORD="${TURISMO_ADMIN_PASSWORD:-}"
SWAP_SIZE_GB="${SWAP_SIZE_GB:-8}"

log() {
    printf '\n==> %s\n' "$*"
}

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_root() {
    [[ "${EUID}" -eq 0 ]] || fail "Ejecuta este script con sudo."
    [[ -n "${ACME_EMAIL}" ]] || fail \
        "Falta ACME_EMAIL. Ejemplo: sudo ACME_EMAIL=correo@dominio.com bash $0"
    [[ "${SWAP_SIZE_GB}" =~ ^[0-9]+$ ]] || fail "SWAP_SIZE_GB debe ser un entero."
    id "${DEPLOY_OWNER}" >/dev/null 2>&1 || fail \
        "El usuario DEPLOY_OWNER=${DEPLOY_OWNER} no existe."
    DEPLOY_GROUP="$(id -gn "${DEPLOY_OWNER}")"
}

install_base_packages() {
    log "Instalando paquetes base"
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        ca-certificates \
        curl \
        git \
        openssl \
        ufw
}

install_docker() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        log "Docker y Docker Compose ya están instalados"
        return
    fi

    log "Instalando Docker Engine desde el repositorio oficial"
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    # shellcheck disable=SC1091
    . /etc/os-release
    printf '%s\n' \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
        > /etc/apt/sources.list.d/docker.list

    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin

    systemctl enable --now docker
    usermod -aG docker "${DEPLOY_OWNER}"
}

configure_docker_logs() {
    if [[ -e /etc/docker/daemon.json ]]; then
        log "Se conserva /etc/docker/daemon.json existente"
        return
    fi

    log "Configurando rotación de logs de Docker"
    install -m 0755 -d /etc/docker
    install -m 0644 /dev/null /etc/docker/daemon.json
    cat > /etc/docker/daemon.json <<'JSON'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
JSON
    systemctl restart docker
}

configure_firewall() {
    log "Configurando UFW para SSH, HTTP y HTTPS"
    ufw allow OpenSSH
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
}

configure_swap() {
    local swap_file="/swapfile"

    if [[ "${SWAP_SIZE_GB}" -eq 0 ]]; then
        log "Creación de swap omitida"
        return
    fi
    if swapon --show=NAME --noheadings | grep -qx "${swap_file}"; then
        log "El swap ${swap_file} ya está activo"
        return
    fi
    if [[ -e "${swap_file}" ]]; then
        log "Se conserva ${swap_file}; no se modifica automáticamente"
        return
    fi

    log "Creando ${SWAP_SIZE_GB} GB de swap"
    fallocate -l "${SWAP_SIZE_GB}G" "${swap_file}"
    chmod 600 "${swap_file}"
    mkswap "${swap_file}"
    swapon "${swap_file}"
    printf '%s\n' "${swap_file} none swap sw 0 0" >> /etc/fstab
}

clone_or_update() {
    local repository="$1"
    local destination="$2"

    install -d -m 0755 "$(dirname "${destination}")"
    if [[ ! -e "${destination}" ]]; then
        git clone "${repository}" "${destination}"
        return
    fi
    [[ -d "${destination}/.git" ]] || fail \
        "${destination} existe pero no es un repositorio Git."
    if [[ -n "$(git -C "${destination}" status --porcelain)" ]]; then
        fail "${destination} tiene cambios locales. No se sobrescribieron."
    fi
    git -C "${destination}" pull --ff-only
}

checkout_repositories() {
    log "Descargando o actualizando repositorios"
    clone_or_update "${CADDY_REPO}" "${CADDY_DIR}"
    clone_or_update "${PRECIOINBOX_REPO}" "${PRECIOINBOX_DIR}"
    clone_or_update "${TURISMO_REPO}" "${TURISMO_DIR}"
    chown -R "${DEPLOY_OWNER}:${DEPLOY_GROUP}" /opt/apps /opt/infra
}

random_hex() {
    openssl rand -hex "$1"
}

write_environments() {
    local postgres_password turismo_secret turismo_password turismo_password_hash
    postgres_password="$(random_hex 24)"
    turismo_secret="$(random_hex 32)"
    turismo_password="${TURISMO_ADMIN_PASSWORD:-$(random_hex 16)}"
    turismo_password_hash="$(printf '%s' "${turismo_password}" | sha256sum | cut -d' ' -f1)"

    log "Creando archivos de entorno que todavía no existan"

    if [[ ! -e "${CADDY_DIR}/.env" ]]; then
        printf 'ACME_EMAIL=%s\n' "${ACME_EMAIL}" > "${CADDY_DIR}/.env"
        chmod 600 "${CADDY_DIR}/.env"
    fi

    if [[ ! -e "${PRECIOINBOX_DIR}/.env" ]]; then
        cat > "${PRECIOINBOX_DIR}/.env" <<EOF
POSTGRES_DB=catalogo
POSTGRES_USER=catalogo
POSTGRES_PASSWORD=${postgres_password}
CORS_ORIGINS=https://precioinbox.com,https://precioinbox.umiphos-arturo.workers.dev
AUTH0_DOMAIN=umiphos.us.auth0.com
AUTH0_AUDIENCE=https://api.precioinbox.com
AUTH0_ALGORITHMS=RS256
SEED_DEMO_DATA=true
EOF
        chmod 600 "${PRECIOINBOX_DIR}/.env"
    fi

    if [[ ! -e "${TURISMO_DIR}/.env" ]]; then
        cat > "${TURISMO_DIR}/.env" <<EOF
CORS_ORIGINS=https://turismo.precioinbox.com
ADMIN_EMAIL=${TURISMO_ADMIN_EMAIL}
ADMIN_PASSWORD_HASH=${turismo_password_hash}
SECRET_KEY=${turismo_secret}
TOKEN_TTL_SECONDS=86400
CONTENT_DB_PATH=/data/content.db
EOF
        chmod 600 "${TURISMO_DIR}/.env"
    fi

    if [[ ! -e "${CREDENTIALS_FILE}" ]]; then
        cat > "${CREDENTIALS_FILE}" <<EOF
Fecha de instalación: $(date --iso-8601=seconds)
Turismo admin: ${TURISMO_ADMIN_EMAIL}
Turismo password: ${turismo_password}

Los secretos de PostgreSQL y de firma están guardados en los .env de cada servicio.
EOF
        chmod 600 "${CREDENTIALS_FILE}"
    fi

    chown "${DEPLOY_OWNER}:${DEPLOY_GROUP}" \
        "${CADDY_DIR}/.env" \
        "${PRECIOINBOX_DIR}/.env" \
        "${TURISMO_DIR}/.env"
}

validate_compose_files() {
    log "Validando configuraciones Docker Compose"
    docker compose --project-directory "${CADDY_DIR}" config --quiet
    docker compose --project-directory "${PRECIOINBOX_DIR}" config --quiet
    docker compose --project-directory "${TURISMO_DIR}" config --quiet
}

start_services() {
    log "Levantando Caddy y la red proxy_network"
    docker compose --project-directory "${CADDY_DIR}" up -d

    log "Construyendo y levantando PrecioInbox"
    docker compose --project-directory "${PRECIOINBOX_DIR}" up -d --build

    log "Construyendo y levantando Turismo"
    docker compose --project-directory "${TURISMO_DIR}" up -d --build
}

verify_services() {
    log "Estado final de los servicios"
    docker compose --project-directory "${CADDY_DIR}" ps
    docker compose --project-directory "${PRECIOINBOX_DIR}" ps
    docker compose --project-directory "${TURISMO_DIR}" ps

    log "Verificando endpoints internos"
    docker compose --project-directory "${PRECIOINBOX_DIR}" exec -T backend \
        python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=10)"
    docker compose --project-directory "${TURISMO_DIR}" exec -T turismo-backend \
        python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=10)"
}

main() {
    require_root
    install_base_packages
    install_docker
    configure_docker_logs
    configure_firewall
    configure_swap
    checkout_repositories
    write_environments
    validate_compose_files
    start_services
    verify_services

    log "Instalación terminada"
    printf 'Credenciales generadas: %s\n' "${CREDENTIALS_FILE}"
    printf 'Cierra sesión y vuelve a entrar para usar Docker sin sudo.\n'
}

main "$@"
