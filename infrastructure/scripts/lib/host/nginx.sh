#!/usr/bin/env bash
set -Eeuo pipefail

configure_host_nginx() {
  [[ "$EUID" -eq 0 ]] || die "Host NGINX configuration requires root privileges."
  require_command nginx
  require_command systemctl

  local hostname loopback_port max_body environment template site_name certificate_name
  local available_site enabled_site rendered_site email
  hostname="$(read_env APP_HOSTNAME)"
  loopback_port="$(read_env RBF_LOOPBACK_PORT)"
  max_body="$(read_env GATEWAY_MAX_BODY_MB)"
  environment="$(read_env DEPLOYMENT_ENVIRONMENT)"
  template="$INFRA_DIR/nginx/host-site.conf"

  [[ "$hostname" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$ ]] || die "APP_HOSTNAME is invalid."
  [[ "$loopback_port" =~ ^[1-9][0-9]{0,4}$ && "$loopback_port" -le 65535 ]] \
    || die "RBF_LOOPBACK_PORT must be between 1 and 65535."
  [[ "$max_body" =~ ^[1-9][0-9]{0,2}$ ]] || max_body=90
  [[ "$environment" == test || "$environment" == production ]] \
    || die "DEPLOYMENT_ENVIRONMENT must be test or production."
  [[ -f "$template" ]] || die "Host NGINX site template is missing: $template"
  [[ -d /etc/nginx/sites-available && -d /etc/nginx/sites-enabled ]] \
    || die "Standard NGINX site directories are missing. Install VPS-Gateway first."

  site_name="rbf-hub-$environment-$hostname.conf"
  certificate_name="rbf-hub-$environment-$hostname"
  available_site="/etc/nginx/sites-available/$site_name"
  enabled_site="/etc/nginx/sites-enabled/$site_name"
  if [[ -e "$available_site" ]]; then
    [[ -f "$available_site" && ! -L "$available_site" ]] \
      || die "Existing host NGINX site is unsafe: $available_site"
    if ! grep -Fq "server_name $hostname;" "$available_site" || \
      ! grep -Fq "proxy_pass http://127.0.0.1:$loopback_port;" "$available_site"; then
      die "Existing host NGINX site does not match this target: $available_site"
    fi
  else
    rendered_site="$(mktemp)"
    sed -e "s/\${APP_HOSTNAME}/$hostname/g" \
      -e "s/\${RBF_LOOPBACK_PORT}/$loopback_port/g" \
      -e "s/\${GATEWAY_MAX_BODY_MB}/$max_body/g" \
      "$template" > "$rendered_site"
    install -m 0644 -o root -g root "$rendered_site" "$available_site"
    rm -f -- "$rendered_site"
  fi
  ln -sfn "$available_site" "$enabled_site"
  nginx -t
  systemctl reload nginx 2>/dev/null || systemctl start nginx

  if [[ "$environment" == production ]] && {
    [[ ! -s "/etc/letsencrypt/live/$certificate_name/fullchain.pem" ]] ||
      ! grep -Eq 'listen[[:space:]]+443[[:space:]]+ssl' "$available_site"
  }; then
    require_command certbot
    email="$(read_env LETSENCRYPT_EMAIL)"
    [[ "$email" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]] \
      || die "Production requires a valid LETSENCRYPT_EMAIL."
    certbot --nginx --redirect --non-interactive --agree-tos --no-eff-email \
      --email "$email" --cert-name "$certificate_name" -d "$hostname"
  fi
}
