#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

mode="${1:-setup}"
[[ "$mode" == setup || "$mode" == runtime ]] || die "Usage: preflight.sh [setup|runtime]"

arch="$(uname -m)"
case "$arch" in
  aarch64|arm64|x86_64|amd64) ;;
  *) die "Nicht unterstützte Architektur: $arch. Für Produktion wird ein 64-Bit-System benötigt." ;;
esac

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  case "${ID:-}" in
    debian|raspbian|ubuntu) ;;
    *) warn "Nicht verifiziertes Betriebssystem: ${PRETTY_NAME:-${ID:-unbekannt}}" ;;
  esac
fi

available_kb="$(df -Pk "$INFRA_DIR" | awk 'NR==2 {print $4}')"
if [[ "$available_kb" =~ ^[0-9]+$ ]] && ((available_kb < 8 * 1024 * 1024)); then
  warn "Weniger als 8 GiB freier Speicher. Container-Builds und Backups können fehlschlagen."
fi

memory_kb="$(awk '/MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || printf 0)"
if [[ "$memory_kb" =~ ^[0-9]+$ ]] && ((memory_kb < 1800000)); then
  warn "Weniger als 2 GiB RAM erkannt. Ein 64-Bit Raspberry Pi mit mindestens 2 GiB wird empfohlen."
fi

if command -v ss >/dev/null 2>&1; then
  for port in 80 443; do
    if ss -H -ltn "sport = :$port" 2>/dev/null | grep -q .; then
      warn "TCP-Port $port wird bereits verwendet. Der Gateway-Container kann dort nicht binden."
    fi
  done
fi

if [[ "$mode" == runtime ]]; then
  require_command docker
  docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1 \
    || die "Docker Compose fehlt."
  ensure_env_file
fi

success "Preflight erfolgreich (${arch}, Modus: ${mode})."
