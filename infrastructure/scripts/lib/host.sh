#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/env.sh"

install_host_dependencies() {
  [[ "$EUID" -eq 0 ]] || die "Host-Provisioning benötigt root-Rechte."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y ca-certificates certbot curl git openssl ufw

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
  mkdir -p "$INFRA_DIR/data"/{postgres,uploads,nginx,certs,backups,uptime-kuma,acme,letsencrypt/config,letsencrypt/work,letsencrypt/logs}

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
  chmod 755 "$INFRA_DIR/data/acme" "$INFRA_DIR/data/certs"
  chmod 700 "$INFRA_DIR/data/letsencrypt" "$INFRA_DIR/data/letsencrypt/config" "$INFRA_DIR/data/letsencrypt/work" "$INFRA_DIR/data/letsencrypt/logs"
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
  if is_true "$(read_env ENABLE_MONITORING)"; then
    local monitoring_port
    monitoring_port="$(read_env MONITORING_HTTPS_PORT)"
    [[ "$monitoring_port" =~ ^[0-9]+$ ]] || monitoring_port=8443
    ufw allow "${monitoring_port}/tcp"
  fi
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
    log "Vorhandenes TLS-Zertifikat wird als Bootstrap-Zertifikat weiterverwendet."
    return
  fi

  cat > "$config_file" <<CERTCFG
[req]
distinguished_name=req_distinguished_name
x509_extensions=v3_req
prompt=no
[req_distinguished_name]
CN=${hostname}
O=Royal Blackwater Vanguards
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
    die "TLS-Bootstrap-Zertifikat konnte nicht erzeugt werden."
  fi
  rm -f "$config_file" "$error_file"
  chmod 600 "$cert_dir/privkey.pem"
  chmod 644 "$cert_dir/fullchain.pem"
  set_env_value CERTIFICATE_PROVIDER self-signed
  success "Selbstsigniertes Bootstrap-Zertifikat für ${hostname} / ${ip} erstellt."
}

is_public_certificate_hostname() {
  local hostname="$1"
  [[ -n "$hostname" && "$hostname" != *.local && ! "$hostname" =~ ^[0-9.]+$ && "$hostname" == *.* ]]
}

request_letsencrypt_certificate() {
  local hostname email cert_name staging_args=()
  hostname="$(read_env APP_HOSTNAME)"
  email="$(read_env LETSENCRYPT_EMAIL)"
  cert_name="$(read_env LETSENCRYPT_CERT_NAME)"
  [[ -n "$cert_name" ]] || cert_name="$hostname"

  if ! command -v certbot >/dev/null 2>&1; then
    warn "Let's Encrypt wurde übersprungen: certbot ist nicht installiert."
    return 1
  fi
  is_public_certificate_hostname "$hostname" || {
    warn "Let's Encrypt wurde übersprungen: ${hostname} ist keine öffentliche Domain."
    return 1
  }
  [[ -n "$email" ]] || {
    warn "Let's Encrypt wurde übersprungen: Kontakt-E-Mail fehlt."
    return 1
  }
  if is_true "$(read_env LETSENCRYPT_STAGING)"; then
    staging_args+=(--staging)
    warn "Let's Encrypt Staging ist aktiv; das Zertifikat ist nicht öffentlich vertrauenswürdig."
  fi

  log "Fordere ein Let's-Encrypt-Zertifikat für ${hostname} an."
  if ! certbot certonly \
      --non-interactive \
      --agree-tos \
      --email "$email" \
      --webroot \
      --webroot-path "$ACME_WEBROOT" \
      --config-dir "$CERTBOT_CONFIG_DIR" \
      --work-dir "$CERTBOT_WORK_DIR" \
      --logs-dir "$CERTBOT_LOGS_DIR" \
      --cert-name "$cert_name" \
      --keep-until-expiring \
      "${staging_args[@]}" \
      -d "$hostname"; then
    warn "Let's Encrypt konnte das Zertifikat nicht ausstellen. Prüfe DNS sowie die Weiterleitung von TCP-Port 80 auf diesen Pi."
    return 1
  fi

  RENEWED_LINEAGE="$CERTBOT_CONFIG_DIR/live/$cert_name" "$INFRA_DIR/scripts/tls/sync-certificate.sh"
}

configure_production_tls() {
  local mode
  mode="$(read_env TLS_MODE)"
  case "$mode" in
    self-signed)
      set_env_value CERTIFICATE_PROVIDER self-signed
      warn "TLS_MODE=self-signed: Browser zeigen eine Zertifikatswarnung."
      ;;
    letsencrypt)
      request_letsencrypt_certificate || die "Let's-Encrypt-Einrichtung ist fehlgeschlagen."
      ;;
    auto)
      if request_letsencrypt_certificate; then
        success "Öffentlich vertrauenswürdiges TLS ist aktiv."
      else
        set_env_value CERTIFICATE_PROVIDER self-signed
        warn "Automatischer TLS-Modus verwendet vorerst das selbstsignierte Zertifikat."
      fi
      ;;
  esac
}
