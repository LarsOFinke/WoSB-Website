#!/usr/bin/env bash
set -Eeuo pipefail

generate_self_signed_certificate() {
  local hostname ip cert_dir config_file error_file
  hostname="$(read_env APP_HOSTNAME)"
  ip="$(read_env APP_IP)"
  cert_dir="$INFRA_DIR/data/certs"

  if [[ -s "$cert_dir/fullchain.pem" && -s "$cert_dir/privkey.pem" ]]; then
    log "Vorhandenes TLS-Zertifikat wird als Bootstrap-Zertifikat weiterverwendet."
    return 0
  fi

  config_file="$(mktemp)"
  error_file="$(mktemp)"
  cat > "$config_file" <<CERTCFG
[req]
distinguished_name=req_distinguished_name
x509_extensions=v3_req
prompt=no
[req_distinguished_name]
CN=${hostname}
O=Royal Blackwater Fleet
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
  if ! is_public_certificate_hostname "$hostname"; then
    warn "Let's Encrypt wurde übersprungen: ${hostname} ist keine öffentliche Domain."
    return 1
  fi
  if [[ -z "$email" ]]; then
    warn "Let's Encrypt wurde übersprungen: Kontakt-E-Mail fehlt."
    return 1
  fi
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

  RENEWED_LINEAGE="$CERTBOT_CONFIG_DIR/live/$cert_name" \
    /usr/bin/env bash "$INFRA_DIR/scripts/tls/sync-certificate.sh"
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
