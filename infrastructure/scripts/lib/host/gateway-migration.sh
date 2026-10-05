#!/usr/bin/env bash
# Shared preflight and handover policy; no containers are stopped during preflight.
set -Eeuo pipefail

host_gateway_initialized() {
  local nginx_root="${1:-/etc/nginx}"
  [[ -f "$nginx_root/conf.d/vps-gateway.conf" &&
     -f "$nginx_root/snippets/vps-gateway-proxy-headers.conf" &&
     -L "$nginx_root/sites-enabled/vps-gateway-catch-all.conf" &&
     -f "$nginx_root/sites-enabled/vps-gateway-catch-all.conf" ]]
}

legacy_public_gateway() {
  local runtime="$1"
  [[ -f "$runtime/compose.release.yml" && ! -f "$runtime/nginx/host-site.conf" ]]
}

preflight_host_gateway() {
  local allow_initialization="${1:-false}" nginx_root="${2:-/etc/nginx}"
  command -v vps-gateway-site-import >/dev/null 2>&1 \
    || { echo '[gateway] Install VPS-Gateway commands before updating; the running stack was not stopped.' >&2; return 1; }
  if host_gateway_initialized "$nginx_root"; then
    nginx -t
    return
  fi
  if [[ "$allow_initialization" != true ]]; then
    echo '[gateway] VPS-Gateway is not initialized. Run sudo vps-gateway-init --empty before a first deployment.' >&2
    return 1
  fi
  command -v vps-gateway-init >/dev/null 2>&1 \
    || { echo '[gateway] Install vps-gateway-init before migrating the public gateway.' >&2; return 1; }
  # The upstream initializer refuses custom/partial cores. Fail before downtime,
  # rather than discovering that condition after replacing the old container.
  local entry
  for entry in "$nginx_root"/conf.d/*.conf "$nginx_root"/sites-enabled/* \
    "$nginx_root/snippets/vps-gateway-proxy-headers.conf" \
    "$nginx_root/sites-available/vps-gateway-catch-all.conf"; do
    [[ -e "$entry" || -L "$entry" ]] || continue
    if [[ "$entry" == "$nginx_root/sites-enabled/default" && -L "$entry" ]]; then
      case "$(readlink "$entry")" in /etc/nginx/sites-available/default|../sites-available/default) continue ;; esac
    fi
    echo '[gateway] Partial or custom host NGINX configuration prevents automatic initialization; complete VPS-Gateway setup before updating.' >&2
    return 1
  done
  echo '[gateway] Legacy migration: host NGINX will be initialized after the project releases ports 80/443.'
}

activate_host_gateway() {
  local allow_initialization="${1:-false}"
  if ! host_gateway_initialized; then
    [[ "$allow_initialization" == true ]] \
      || { echo '[gateway] VPS-Gateway is not initialized.' >&2; return 1; }
    vps-gateway-init --empty
  fi
  host_gateway_initialized \
    || { echo '[gateway] VPS-Gateway initialization did not create a complete core.' >&2; return 1; }
  nginx -t
  systemctl enable --now nginx
}
