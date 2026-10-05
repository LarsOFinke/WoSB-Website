#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
fail() { echo "[host-nginx] $*" >&2; exit 1; }

compose_files=("$ROOT_DIR/infrastructure/compose.yml" "$ROOT_DIR/infrastructure/compose.release.yml")
for compose in "${compose_files[@]}"; do
  gateway="$(sed -n '/^  gateway:/,/^networks:/p' "$compose")"
  grep -Fq '127.0.0.1:${RBF_LOOPBACK_PORT:-18080}:8080' <<< "$gateway" \
    || fail "$compose must bind only the configured loopback port"
  grep -Fq 'ports:' <<< "$gateway" || fail "$compose gateway port is missing"
  ! grep -Eq '443:8443|80:8080|certs:/etc/nginx/certs|acme:/var/www/certbot' <<< "$gateway" \
    || fail "$compose still makes the project container own public HTTP/TLS"
done

host_site="$ROOT_DIR/infrastructure/nginx/host-site.conf"
grep -Fq 'listen 80;' "$host_site" || fail 'host site must accept HTTP for routing and certificate validation'
grep -Fq 'listen [::]:80;' "$host_site" || fail 'host site must support IPv6 DNS targets'
grep -Fq 'proxy_pass http://127.0.0.1:${RBF_LOOPBACK_PORT};' "$host_site" \
  || fail 'host site must route to the private loopback port'
grep -Fq 'include /etc/nginx/snippets/vps-gateway-proxy-headers.conf;' "$host_site" \
  || fail 'host site must use the VPS-Gateway trusted proxy headers'
grep -Fq 'access_log /var/log/nginx/access.log vps_gateway;' "$host_site" \
  || fail 'host site must use the gateway query-free log format'
grep -Fq 'limit_req zone=gateway_per_ip' "$host_site" \
  || fail 'host site must participate in the gateway request limits'

gateway_conf="$ROOT_DIR/infrastructure/nginx/default.conf"
grep -Fq 'map $http_x_real_ip $rbf_client_ip' "$gateway_conf" \
  || fail 'project rate limits must use the host-forwarded client address'
grep -Fq 'map $http_x_forwarded_proto $rbf_forwarded_proto' "$gateway_conf" \
  || fail 'application must receive the browser-facing scheme'
grep -Fq 'X-Forwarded-Proto $rbf_forwarded_proto;' "$gateway_conf" \
  || fail 'API proxy must retain the trusted external scheme'
! grep -Eq 'listen 8443|ssl_certificate|/var/www/certbot|return 308 https://' "$gateway_conf" \
  || fail 'project gateway must not own public TLS or redirects'

host_integration="$ROOT_DIR/infrastructure/scripts/lib/host/nginx.sh"
grep -Fq 'nginx -t' "$host_integration" \
  || fail 'host site provisioning must validate NGINX before reload'
grep -Fq 'vps-gateway-site-import --host "$hostname" --file "$rendered_site"' "$host_integration" \
  || fail 'new sites must be installed through VPS-Gateway'
grep -Fq 'VPS-Gateway is not initialized' "$host_integration" \
  || fail 'host site integration must check the gateway core'
grep -Fq 'preflight_host_gateway' "$ROOT_DIR/infrastructure/scripts/release/setup_website.sh" \
  || fail 'the target must check VPS-Gateway before backup and release activation'
grep -Fq 'legacy_site=' "$host_integration" \
  || fail 'existing project sites must be preserved during migration'
grep -Fq 'certbot --nginx --redirect' "$host_integration" \
  || fail 'production certificate must be installed by the host NGINX integration'
grep -Fq "! grep -Eq 'listen[[:space:]]+443[[:space:]]+ssl' \"\$available_site\"" "$host_integration" \
  || fail 'an existing certificate must still be installed into a site without TLS'
grep -Fq 'site_name="$hostname.conf"' "$host_integration" \
  || fail 'new sites must use VPS-Gateway hostname naming'
grep -Fq 'RBF_LOOPBACK_PORT=18080' "$ROOT_DIR/infrastructure/.env.example" \
  || fail 'runtime needs a documented default private port'
grep -Fq -- '--resolve "${hostname}:${public_port}:127.0.0.1"' "$ROOT_DIR/infrastructure/scripts/checks/smoke-test.sh" \
  || fail 'health checks must probe the local host listener without depending on external IPv4/IPv6 routing'

printf '[host-nginx] OK: private project bind, hostname proxy and host-managed TLS\n'
