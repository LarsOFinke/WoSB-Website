#!/usr/bin/env bash
set -Eeuo pipefail

configure_host_nginx() {
  [[ "$EUID" -eq 0 ]] || die "Host NGINX configuration requires root privileges."
  require_command nginx

  local hostname loopback_port max_body environment template site_name certificate_name
  local available_site enabled_site rendered_site email legacy_site
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
  require_command vps-gateway-site-import
  [[ -f /etc/nginx/conf.d/vps-gateway.conf &&
     -f /etc/nginx/snippets/vps-gateway-proxy-headers.conf &&
     -L /etc/nginx/sites-enabled/vps-gateway-catch-all.conf ]] \
    || die "VPS-Gateway is not initialized. Initialize its core and catch-all before deploying this site."

  site_name="$hostname.conf"
  certificate_name="rbf-hub-$environment-$hostname"
  available_site="/etc/nginx/sites-available/$site_name"
  enabled_site="/etc/nginx/sites-enabled/$site_name"
  legacy_site="/etc/nginx/sites-available/rbf-hub-$environment-$hostname.conf"
  if [[ -e "$legacy_site" || -L "$legacy_site" ]]; then
    [[ ! -e "$available_site" && ! -L "$available_site" ]] \
      || die "Both legacy and VPS-Gateway sites exist for $hostname; review the duplicate hostname."
    available_site="$legacy_site"
    enabled_site="/etc/nginx/sites-enabled/$(basename "$legacy_site")"
  fi
  if [[ -e "$available_site" ]]; then
    [[ -f "$available_site" && ! -L "$available_site" ]] \
      || die "Existing host NGINX site is unsafe: $available_site"
    [[ -L "$enabled_site" && "$(readlink -f "$enabled_site")" == "$available_site" ]] \
      || die "Existing host NGINX site is not enabled as expected: $enabled_site"
    if ! grep -Fq "server_name $hostname;" "$available_site" || \
      ! grep -Fq "proxy_pass http://127.0.0.1:$loopback_port;" "$available_site"; then
      die "Existing host NGINX site does not match the hostname and loopback port. Update the custom site and rerun: $available_site"
    fi
    nginx -t
  else
    rendered_site="$(mktemp)"
    sed -e "s/\${APP_HOSTNAME}/$hostname/g" \
      -e "s/\${RBF_LOOPBACK_PORT}/$loopback_port/g" \
      -e "s/\${GATEWAY_MAX_BODY_MB}/$max_body/g" \
      "$template" > "$rendered_site"
    if ! vps-gateway-site-import --host "$hostname" --file "$rendered_site"; then
      rm -f -- "$rendered_site"
      die "VPS-Gateway could not import the project site for $hostname."
    fi
    rm -f -- "$rendered_site"
  fi

  if [[ "$environment" == production ]] &&
    ! grep -Eq 'listen[[:space:]]+443[[:space:]]+ssl' "$available_site"; then
    require_command certbot
    email="$(read_env LETSENCRYPT_EMAIL)"
    [[ "$email" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]] \
      || die "Production requires a valid LETSENCRYPT_EMAIL."
    certbot --nginx --redirect --non-interactive --agree-tos --no-eff-email \
      --email "$email" --cert-name "$certificate_name" -d "$hostname"
  fi
}
