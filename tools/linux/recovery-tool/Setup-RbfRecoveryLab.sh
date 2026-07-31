#!/usr/bin/env bash
set -Eeuo pipefail

[[ "$EUID" -ne 0 ]] || { echo "Dieses Skript muss als normaler Benutzer laufen." >&2; exit 1; }
BINARY="${1:-${HOME}/.local/bin/rbf-recovery-tool}"
[[ -x "$BINARY" ]] || { echo "Recovery-Tool nicht gefunden: $BINARY" >&2; exit 1; }
command -v dockerd-rootless-setuptool.sh >/dev/null 2>&1 || {
  echo "Rootless-Docker-Werkzeug fehlt. Zuerst Provision-RbfRecoveryLab.sh ausführen." >&2
  exit 1
}

previous_context="$(docker context show 2>/dev/null || true)"
if ! docker context inspect rootless >/dev/null 2>&1; then
  dockerd-rootless-setuptool.sh install --force
fi
systemctl --user enable --now docker.service

for attempt in $(seq 1 30); do
  docker --context rootless info >/dev/null 2>&1 && break
  sleep 1
  if [[ "$attempt" -eq 30 ]]; then
    echo "Rootless Docker wurde nicht rechtzeitig bereit." >&2
    exit 1
  fi
done

security_options="$(docker --context rootless info --format '{{json .SecurityOptions}}')"
grep -qi rootless <<<"$security_options" || {
  echo "Der aktive Docker-Kontext ist nicht rootless; Einrichtung abgebrochen." >&2
  exit 1
}

if [[ -n "$previous_context" ]] && docker context inspect "$previous_context" >/dev/null 2>&1; then
  docker context use "$previous_context" >/dev/null
fi
"$BINARY" lab init
"$BINARY" lab start
printf 'Lokales RBF-PostgreSQL-Recovery-Labor ist bereit.\n'
