#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/common.sh"

mode="${1:-setup}"
[[ "$mode" == setup || "$mode" == runtime ]] || die "Usage: preflight.sh [setup|runtime]"

arch="$(uname -m)"
case "$arch" in
  aarch64|arm64|x86_64|amd64) ;;
  *) die "Unsupported architecture: $arch. Production requires a 64-bit system." ;;
esac

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  case "${ID:-}" in
    debian|raspbian|ubuntu) ;;
    *) warn "Unverified operating system: ${PRETTY_NAME:-${ID:-unknown}}" ;;
  esac
fi

available_kb="$(df -Pk "$INFRA_DIR" | awk 'NR==2 {print $4}')"
if [[ "$available_kb" =~ ^[0-9]+$ ]] && ((available_kb < 8 * 1024 * 1024)); then
  warn "Less than 8 GiB of free storage. Container builds and backups may fail."
fi

memory_kb="$(awk '/MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || printf 0)"
if [[ "$memory_kb" =~ ^[0-9]+$ ]] && ((memory_kb < 1800000)); then
  warn "Less than 2 GiB RAM detected. A 64-bit Raspberry Pi with at least 2 GiB is recommended."
fi

if command -v ss >/dev/null 2>&1; then
  for port in 80 443; do
    if ss -H -ltn "sport = :$port" 2>/dev/null | grep -q .; then
      warn "TCP port $port is already in use. The gateway container cannot bind there."
    fi
  done
fi

if [[ "$mode" == runtime ]]; then
  require_command docker
  docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1 \
    || die "Docker Compose is missing."
  ensure_env_file
fi

success "Preflight succeeded (${arch}, mode: ${mode})."
