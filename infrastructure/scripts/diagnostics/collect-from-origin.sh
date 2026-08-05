#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
config_file="${RBF_ORIGIN_CONFIG:-$ROOT_DIR/.env.origin}"
area=""; category=""; since="30m"; tail_lines="400"; match=""; output=""

usage() {
  cat <<'EOF'
Usage: infrastructure/scripts/diagnostics/debug.sh [OPTIONS]

Collects a bounded, redacted diagnostic log on the origin system through the
existing deployment SSH identity. Without --area an interactive menu is shown.

  --area AREA          overview|staff|calendar|api|security|gateway|database|deployment|all
  --category CATEGORY  errors|warnings|http-500|auth|migration|all (default: errors)
  --since DURATION     positive duration such as 15m, 2h or 1d (default: 30m)
  --tail LINES         maximum lines per remote source, 1..2000 (default: 400)
  --match TEXT         optional additional literal match, maximum 120 characters
  --output FILE        local output path; '-' writes only to stdout
  --config FILE        origin connection file (default: .env.origin)
EOF
}

while (($#)); do
  case "$1" in
    --area) area="${2:-}"; shift 2 ;;
    --category) category="${2:-}"; shift 2 ;;
    --since) since="${2:-}"; shift 2 ;;
    --tail) tail_lines="${2:-}"; shift 2 ;;
    --match) match="${2:-}"; shift 2 ;;
    --output) output="${2:-}"; shift 2 ;;
    --config) config_file="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

choose_area() {
  local choice
  printf '%s\n' \
    'Diagnosebereich:' \
    '  1) Übersicht / Dienststatus' \
    '  2) Staff-Panel' \
    '  3) Kalender und Raid-Helper' \
    '  4) Spring API' \
    '  5) Security / 401 / 403' \
    '  6) Gateway / NGINX' \
    '  7) PostgreSQL' \
    '  8) Deployment / systemd' \
    '  9) Alle Laufzeitdienste'
  read -r -p 'Auswahl [3]: ' choice
  case "${choice:-3}" in
    1) area=overview ;; 2) area=staff ;; 3) area=calendar ;; 4) area=api ;;
    5) area=security ;; 6) area=gateway ;; 7) area=database ;;
    8) area=deployment ;; 9) area=all ;; *) echo '[debug] Ungültige Auswahl.' >&2; exit 2 ;;
  esac
}

choose_category() {
  local choice
  printf '%s\n' \
    'Logkategorie:' \
    '  1) Fehler' \
    '  2) Warnungen und Fehler' \
    '  3) Nur HTTP 500' \
    '  4) Authentifizierung / Autorisierung' \
    '  5) Migration / Schema' \
    '  6) Alle Einträge im Bereich'
  read -r -p 'Auswahl [1]: ' choice
  case "${choice:-1}" in
    1) category=errors ;; 2) category=warnings ;; 3) category=http-500 ;;
    4) category=auth ;; 5) category=migration ;; 6) category=all ;;
    *) echo '[debug] Ungültige Auswahl.' >&2; exit 2 ;;
  esac
}

if [[ -z "$area" ]]; then
  [[ -t 0 && -t 1 ]] || { echo '[debug] Ohne interaktives Terminal ist --area erforderlich.' >&2; exit 2; }
  choose_area
  [[ "$area" == overview ]] || choose_category
  read -r -p "Zeitraum [${since}]: " answer; since="${answer:-$since}"
  read -r -p "Maximale Zeilen je Quelle [${tail_lines}]: " answer; tail_lines="${answer:-$tail_lines}"
  read -r -p 'Zusätzlicher Suchtext (optional): ' match
fi
category="${category:-errors}"

case "$area" in overview|staff|calendar|api|security|gateway|database|deployment|all) ;; *) echo "[debug] Ungültiger Bereich: $area" >&2; exit 2 ;; esac
case "$category" in errors|warnings|http-500|auth|migration|all) ;; *) echo "[debug] Ungültige Kategorie: $category" >&2; exit 2 ;; esac
[[ "$since" =~ ^[1-9][0-9]*(m|h|d)$ ]] || { echo "[debug] Ungültiger Zeitraum: $since" >&2; exit 2; }
[[ "$tail_lines" =~ ^[0-9]+$ && "$tail_lines" -ge 1 && "$tail_lines" -le 2000 ]] \
  || { echo '[debug] --tail muss zwischen 1 und 2000 liegen.' >&2; exit 2; }
[[ "$match" != *$'\n'* && ${#match} -le 120 ]] || { echo '[debug] --match ist zu lang oder mehrzeilig.' >&2; exit 2; }
[[ -f "$config_file" ]] || { echo "[debug] Origin-Konfiguration fehlt: $config_file" >&2; exit 1; }

# .env.origin is an owner-only shell configuration created by deploy.sh.
# shellcheck disable=SC1090
source "$config_file"
host="${RBF_DEPLOY_HOST:-}"; user="${RBF_DEPLOY_USER:-rbfadmin}"
port="${RBF_DEPLOY_PORT:-22}"; identity_file="${RBF_DEPLOY_IDENTITY_FILE:-}"
install_root="${RBF_DEPLOY_INSTALL_ROOT:-/srv/rbf}"
if [[ -z "$identity_file" && -n "${HOME:-}" && -f "$HOME/.ssh/$user" ]]; then identity_file="$HOME/.ssh/$user"; fi
[[ -n "$host" ]] || { echo '[debug] RBF_DEPLOY_HOST fehlt in der Origin-Konfiguration.' >&2; exit 1; }
[[ "$user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] || { echo '[debug] Ungültiger SSH-Benutzer.' >&2; exit 2; }
[[ "$port" =~ ^[0-9]+$ && "$port" -le 65535 ]] || { echo '[debug] Ungültiger SSH-Port.' >&2; exit 2; }
[[ "$install_root" == /* ]] || { echo '[debug] Installationsroot muss absolut sein.' >&2; exit 2; }
[[ -z "$identity_file" || -f "$identity_file" ]] || { echo "[debug] SSH-Identity fehlt: $identity_file" >&2; exit 1; }
for command in ssh python3; do command -v "$command" >/dev/null 2>&1 || { echo "[debug] Kommando fehlt: $command" >&2; exit 1; }; done

ssh_args=(-o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 -p "$port")
[[ -z "$identity_file" ]] || ssh_args+=(-i "$identity_file")
remote_command=(sudo -n /usr/bin/env bash -s -- --install-root "$install_root" --area "$area" --category "$category" --since "$since" --tail "$tail_lines")
[[ -z "$match" ]] || remote_command+=(--match "$match")
remote_line=""
for word in "${remote_command[@]}"; do printf -v quoted ' %q' "$word"; remote_line+="$quoted"; done

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -z "$output" ]]; then output="$ROOT_DIR/.diagnostics/${timestamp}-${area}-${category}.log"; fi
collect() {
  printf 'RBF_ORIGIN_DIAGNOSTIC=1\ncollected_at=%s\narea=%s\ncategory=%s\nsince=%s\ntail=%s\n' \
    "$timestamp" "$area" "$category" "$since" "$tail_lines"
  # remote_line is assembled with printf %q from validated arguments.
  # shellcheck disable=SC2029
  ssh "${ssh_args[@]}" "$user@$host" "$remote_line" < "$SCRIPT_DIR/collect-remote.sh"
}

if [[ "$output" == '-' ]]; then
  collect | python3 "$SCRIPT_DIR/redact.py"
  exit 0
fi
[[ "$output" == /* ]] || output="$ROOT_DIR/$output"
[[ ! -e "$output" ]] || { echo "[debug] Ausgabedatei existiert bereits: $output" >&2; exit 1; }
install -d -m 0700 "$(dirname "$output")"
umask 077
temporary="${output}.tmp.$$"
cleanup() { rm -f -- "$temporary"; }
trap cleanup EXIT
collect | python3 "$SCRIPT_DIR/redact.py" > "$temporary"
mv -f "$temporary" "$output"
trap - EXIT
line_count="$(wc -l < "$output")"
printf '[debug] Redigierte Diagnose lokal gespeichert: %s (%s Zeilen)\n' "$output" "$line_count" >&2
