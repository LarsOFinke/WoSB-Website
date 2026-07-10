#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

install_host_dependencies() {
  [[ "$EUID" -eq 0 ]] || die "Host-Provisioning benötigt root-Rechte."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y ca-certificates curl git openssl ufw

  if ! command -v docker >/dev/null 2>&1; then
    apt-get install -y docker.io
  fi

  if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
    apt-get install -y docker-compose-plugin 2>/dev/null \
      || apt-get install -y docker-compose-v2 2>/dev/null \
      || apt-get install -y docker-compose
  fi

  systemctl enable --now docker
  local target_user="${SUDO_USER:-}"
  if [[ -n "$target_user" && "$target_user" != root ]]; then
    usermod -aG docker "$target_user"
  fi
}

prepare_data_directories() {
  mkdir -p "$INFRA_DIR/data"/{postgres,uploads,nginx,certs,backups,uptime-kuma}

  # The first infrastructure alpha tracked data/postgres/.gitkeep. PostgreSQL
  # initdb requires a completely empty target directory. Remove only that
  # harmless repository marker and preserve every real database file.
  rm -f "$INFRA_DIR/data/postgres/.gitkeep"

  # A valid existing cluster contains PG_VERSION. For a fresh installation the
  # directory must otherwise be empty; fail early with a useful message instead
  # of waiting for the PostgreSQL healthcheck to time out.
  if [[ ! -f "$INFRA_DIR/data/postgres/PG_VERSION" ]]; then
    local unexpected_entry=""
    unexpected_entry="$(find "$INFRA_DIR/data/postgres" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null || true)"
    [[ -z "$unexpected_entry" ]] || die \
      "PostgreSQL-Datenverzeichnis ist vor der Initialisierung nicht leer: $unexpected_entry"
  fi

  if [[ "$EUID" -eq 0 ]]; then
    chown -R 70:70 "$INFRA_DIR/data/postgres"
    chown -R 10001:10001 "$INFRA_DIR/data/uploads"
    chown -R 101:101 "$INFRA_DIR/data/nginx"
    chown -R 1000:1000 "$INFRA_DIR/data/uptime-kuma"
  fi
  chmod 750 "$INFRA_DIR/data/postgres" "$INFRA_DIR/data/uploads" "$INFRA_DIR/data/backups"
}

detect_ssh_port() {
  local port=""
  if command -v sshd >/dev/null 2>&1; then
    port="$(sshd -T 2>/dev/null | awk '$1 == "port" {print $2; exit}' || true)"
  fi
  if [[ ! "$port" =~ ^[0-9]+$ && -r /etc/ssh/sshd_config ]]; then
    port="$(awk 'tolower($1) == "port" {print $2; exit}' /etc/ssh/sshd_config || true)"
  fi
  [[ "$port" =~ ^[0-9]+$ ]] || port=22
  printf '%s' "$port"
}

configure_firewall() {
  [[ "$EUID" -eq 0 ]] || { warn "Firewall-Konfiguration übersprungen (keine root-Rechte)."; return; }
  local ssh_port
  ssh_port="$(detect_ssh_port)"
  ufw allow "${ssh_port}/tcp"
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
}

generate_self_signed_certificate() {
  local hostname ip cert_dir config_file error_file
  hostname="$(read_env APP_HOSTNAME)"
  ip="$(read_env APP_IP)"
  cert_dir="$INFRA_DIR/data/certs"
  config_file="$(mktemp)"
  error_file="$(mktemp)"

  if [[ -s "$cert_dir/fullchain.pem" && -s "$cert_dir/privkey.pem" ]]; then
    log "Vorhandenes TLS-Zertifikat wird weiterverwendet."
    return
  fi

  cat > "$config_file" <<CERTCFG
[req]
distinguished_name=req_distinguished_name
x509_extensions=v3_req
prompt=no
[req_distinguished_name]
CN=${hostname}
O=Blackwater Mercenaries Hub
[v3_req]
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=@alt_names
[alt_names]
DNS.1=${hostname}
IP.1=${ip}
CERTCFG

  if ! openssl req -x509 -nodes -newkey rsa:4096 -days 825 \
      -keyout "$cert_dir/privkey.pem" \
      -out "$cert_dir/fullchain.pem" \
      -config "$config_file" 2>"$error_file"; then
    cat "$error_file" >&2
    rm -f "$config_file" "$error_file"
    die "TLS-Zertifikat konnte nicht erzeugt werden."
  fi
  rm -f "$config_file" "$error_file"
  chmod 600 "$cert_dir/privkey.pem"
  chmod 644 "$cert_dir/fullchain.pem"
  success "Selbstsigniertes TLS-Zertifikat für ${hostname} / ${ip} erstellt."
}
