#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"

[[ "$EUID" -eq 0 ]] || die "Discord-Bot-Gateway-Konfiguration benötigt root-Rechte."
require_command docker
require_command python3

MODE="${RBF_DISCORD_BOT_FIREWALL_MODE:-auto}"
BIND_HOST="${RBF_DISCORD_BOT_BIND_HOST:-0.0.0.0}"
BOT_PORT=8765
CHECK_ONLY=false
CONFIGURE_ONLY=false
case "${1:-}" in
  "") ;;
  --check-only) CHECK_ONLY=true ;;
  --configure-only) CONFIGURE_ONLY=true ;;
  *) die "Unbekannte Option: ${1:-}" ;;
esac

case "$MODE" in
  auto|external) ;;
  *) die "RBF_DISCORD_BOT_FIREWALL_MODE muss 'auto' oder 'external' sein." ;;
esac
python3 - "$BIND_HOST" <<'PY'
import ipaddress
import sys

address = ipaddress.ip_address(sys.argv[1])
if address.is_loopback:
    raise SystemExit("Der Discord-Bot darf für den Docker-Gateway-Zugriff nicht an eine Loopback-Adresse gebunden sein.")
if address.version != 4:
    raise SystemExit("Der Discord-Bot-Gateway unterstützt aktuell nur eine IPv4-Bind-Adresse.")
PY

GATEWAY_ID="$(bw_compose ps -q gateway 2>/dev/null || true)"
[[ -n "$GATEWAY_ID" ]] || die "Der Website-Gateway-Container läuft nicht. Zuerst den Website-Stack starten."

HOST_GATEWAY_IP="$(docker exec "$GATEWAY_ID" sh -lc "awk '\$2 == \"host.docker.internal\" { print \$1; exit }' /etc/hosts" 2>/dev/null || true)"
[[ -n "$HOST_GATEWAY_IP" ]] || die "host.docker.internal ist im Gateway-Container nicht auflösbar."

python3 - "$HOST_GATEWAY_IP" <<'PY'
import ipaddress
import sys

address = ipaddress.ip_address(sys.argv[1])
if address.version != 4 or not address.is_private:
    raise SystemExit("Die Docker-Host-Gateway-Adresse muss eine private IPv4-Adresse sein.")
PY

mapfile -t GATEWAY_NETWORKS < <(
  docker inspect "$GATEWAY_ID" \
    --format '{{range $name,$network := .NetworkSettings.Networks}}{{println $name}}{{end}}' \
    | sed '/^[[:space:]]*$/d'
)
((${#GATEWAY_NETWORKS[@]} > 0)) || die "Der Gateway-Container besitzt keine Docker-Netzwerke."

mapfile -t GATEWAY_SUBNETS < <(
  for network in "${GATEWAY_NETWORKS[@]}"; do
    docker network inspect "$network" \
      --format '{{range .IPAM.Config}}{{println .Subnet}}{{end}}' 2>/dev/null || true
  done \
    | sed '/^[[:space:]]*$/d' \
    | sort -u
)

VALID_SUBNETS=()
for subnet in "${GATEWAY_SUBNETS[@]}"; do
  if python3 - "$subnet" <<'PY' >/dev/null 2>&1
import ipaddress
import sys
network = ipaddress.ip_network(sys.argv[1], strict=False)
raise SystemExit(0 if network.version == 4 and network.is_private else 1)
PY
  then
    VALID_SUBNETS+=("$subnet")
  fi
done
((${#VALID_SUBNETS[@]} > 0)) || die "Für den Gateway-Container wurde kein privates IPv4-Subnetz gefunden."

firewall_rule_present() {
  local subnet="$1"
  LC_ALL=C ufw status 2>/dev/null \
    | awk -v subnet="$subnet" -v target="$HOST_GATEWAY_IP" -v port="${BOT_PORT}/tcp" '
        index($0, subnet) && index($0, target) && index($0, port) { found = 1 }
        END { exit found ? 0 : 1 }
      '
}

if [[ "$CHECK_ONLY" != true ]]; then
  if [[ "$MODE" == auto ]]; then
    require_command ufw
    LC_ALL=C ufw status 2>/dev/null | grep -q '^Status: active' \
      || die "UFW ist nicht aktiv. Aktiviere UFW oder setze RBF_DISCORD_BOT_FIREWALL_MODE=external bei einer extern verwalteten Firewall."

    for subnet in "${VALID_SUBNETS[@]}"; do
      if firewall_rule_present "$subnet"; then
        log "UFW-Zugriff für Gateway-Subnetz $subnet auf ${HOST_GATEWAY_IP}:${BOT_PORT} ist bereits vorhanden."
      else
        log "Erlaube Gateway-Subnetz $subnet auf ${HOST_GATEWAY_IP}:${BOT_PORT}."
        ufw allow from "$subnet" to "$HOST_GATEWAY_IP" port "$BOT_PORT" proto tcp comment 'RBF Discord bot gateway'
      fi
    done
  else
    warn "Lokale UFW-Verwaltung ist deaktiviert. Die externe Firewall muss ${HOST_GATEWAY_IP}:${BOT_PORT} ausschließlich für die Website-Docker-Netze erlauben."
  fi
fi

if [[ "$CONFIGURE_ONLY" == true ]]; then
  success "Discord-Bot-Gateway-Zugriff ist für ${HOST_GATEWAY_IP}:${BOT_PORT} vorbereitet."
  exit 0
fi

log "Prüfe Discord-Bot-Erreichbarkeit aus dem Website-Gateway."
HEALTH_RESPONSE=""
for _ in $(seq 1 12); do
  if HEALTH_RESPONSE="$(
    docker exec "$GATEWAY_ID" sh -lc \
      "wget -qO- -T 5 http://host.docker.internal:${BOT_PORT}/health" 2>/dev/null
  )"; then
    if python3 - "$HEALTH_RESPONSE" <<'PY' >/dev/null 2>&1
import json
import sys
payload = json.loads(sys.argv[1])
raise SystemExit(0 if payload.get("status") == "ok" else 1)
PY
    then
      success "Discord-Bot ist aus dem Website-Gateway unter ${HOST_GATEWAY_IP}:${BOT_PORT} erreichbar."
      exit 0
    fi
  fi
  sleep 1
done

die "Der Discord-Bot ist aus dem Website-Gateway unter host.docker.internal:${BOT_PORT} nicht erreichbar. Prüfe Dienststatus, Bind-Adresse und UFW-Regeln."
