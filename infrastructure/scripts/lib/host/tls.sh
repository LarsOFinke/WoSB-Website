#!/usr/bin/env bash
set -Eeuo pipefail


verify_tls_material() {
  local certificate="$1" private_key="$2" hostname="$3" minimum_seconds="${4:-604800}"
  [[ -s "$certificate" && -s "$private_key" ]] || die "TLS certificate or private key is missing."
  require_command openssl
  # OpenSSL versions differ in whether `x509 -checkhost` returns a non-zero
  # status for a hostname mismatch. Fail closed unless the command both succeeds
  # and explicitly reports a positive hostname match.
  local hostname_check
  if ! hostname_check="$(openssl x509 -in "$certificate" -noout -checkhost "$hostname" 2>&1)" \
      || [[ "$hostname_check" != *"does match certificate"* ]]; then
    die "TLS certificate is not valid for APP_HOSTNAME=$hostname."
  fi
  local cert_key private_key_fingerprint
  cert_key="$(openssl x509 -in "$certificate" -pubkey -noout | openssl pkey -pubin -outform DER 2>/dev/null | sha256sum | awk '{print $1}')"
  private_key_fingerprint="$(openssl pkey -in "$private_key" -pubout -outform DER 2>/dev/null | sha256sum | awk '{print $1}')"
  [[ -n "$cert_key" && "$cert_key" == "$private_key_fingerprint" ]] \
    || die "TLS certificate and private key do not match."
  openssl x509 -in "$certificate" -checkend "$minimum_seconds" -noout >/dev/null 2>&1 \
    || die "TLS certificate is expired or below the minimum remaining validity."
}

generate_self_signed_certificate() {
  local hostname ip cert_dir config_file error_file
  hostname="$(read_env APP_HOSTNAME)"
  ip="$(read_env APP_IP)"
  cert_dir="$INFRA_DIR/data/certs"

  if [[ -s "$cert_dir/fullchain.pem" && -s "$cert_dir/privkey.pem" ]]; then
    log "Existing TLS certificate will continue to be used as the bootstrap certificate."
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
    die "TLS bootstrap certificate could not be created."
  fi

  rm -f "$config_file" "$error_file"
  chown 0:101 "$cert_dir/privkey.pem"
  chmod 640 "$cert_dir/privkey.pem"
  chmod 644 "$cert_dir/fullchain.pem"
  set_env_value CERTIFICATE_PROVIDER self-signed
  success "Self-signed bootstrap certificate created for ${hostname} / ${ip}."
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
    warn "Let's Encrypt skipped: certbot is not installed."
    return 1
  fi
  if ! is_public_certificate_hostname "$hostname"; then
    warn "Let's Encrypt skipped: ${hostname} is not a public domain."
    return 1
  fi
  if [[ -z "$email" ]]; then
    warn "Let's Encrypt skipped: contact email is missing."
    return 1
  fi
  if is_true "$(read_env LETSENCRYPT_STAGING)"; then
    staging_args+=(--staging)
    warn "Let's Encrypt staging is active; the certificate is not publicly trusted."
  fi

  log "Requesting a Let's Encrypt certificate for ${hostname}."
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
    warn "Let's Encrypt could not issue the certificate. Check DNS and forwarding of TCP port 80 to this Pi."
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
      warn "TLS_MODE=self-signed: browsers display a certificate warning."
      ;;
    letsencrypt)
      request_letsencrypt_certificate || die "Let's Encrypt setup failed."
      ;;
    auto)
      if request_letsencrypt_certificate; then
        success "Publicly trusted TLS is active."
      else
        set_env_value CERTIFICATE_PROVIDER self-signed
        warn "Automatic TLS mode is using the self-signed certificate for now."
      fi
      ;;
  esac
}
