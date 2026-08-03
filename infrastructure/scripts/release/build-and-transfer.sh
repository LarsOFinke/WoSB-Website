#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BUILDER="$SCRIPT_DIR/build-artifact.sh"

usage() {
  cat >&2 <<'USAGE'
Usage:
  build-and-transfer.sh (--target USER@HOST | --user USER --host HOST) [options]

Options:
  --target USER@HOST       SSH destination (required)
  --user USER              SSH username (alternative to --target)
  --host HOST              SSH hostname/address (used with --user)
  --output-dir DIR         Local artifact directory (default: ROOT/release)
  --remote-dir DIR         Remote artifact directory (default: /tmp/rbf-releases)
  --platform PLATFORM      Docker platform, e.g. linux/amd64 or linux/arm64
  --components LIST        api,secure-api,gateway (default: all)
  --port PORT              SSH port (default: 22)
  --identity FILE          SSH private key
  -h, --help               Show this help
USAGE
  exit 2
}

die() { echo "[error] $*" >&2; exit 1; }

output_dir="$ROOT_DIR/release"
remote_dir="/tmp/rbf-releases"
platform=""
components="api,secure-api,gateway"
target=""
user=""
host=""
port="22"
identity=""

while (($#)); do
  case "$1" in
    --target) target="${2:-}"; shift 2 ;;
    --user) user="${2:-}"; shift 2 ;;
    --host) host="${2:-}"; shift 2 ;;
    --output-dir) output_dir="${2:-}"; shift 2 ;;
    --remote-dir) remote_dir="${2:-}"; shift 2 ;;
    --platform) platform="${2:-}"; shift 2 ;;
    --components) components="${2:-}"; shift 2 ;;
    --port) port="${2:-}"; shift 2 ;;
    --identity) identity="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

if [[ -n "$user" || -n "$host" ]]; then
  [[ -n "$user" && -n "$host" ]] || die "--user und --host müssen gemeinsam gesetzt werden."
  [[ -z "$target" ]] || die "--target darf nicht gemeinsam mit --user/--host verwendet werden."
  target="$user@$host"
fi
[[ -n "$target" ]] || die "--target USER@HOST oder --user USER --host HOST ist erforderlich."
[[ -x "$BUILDER" ]] || die "Release-Builder fehlt oder ist nicht ausführbar: $BUILDER"
[[ "$remote_dir" == /* && "$remote_dir" != *$'\n'* && "$remote_dir" != *' '* ]] \
  || die "--remote-dir muss ein absoluter Pfad ohne Leerzeichen sein."
[[ "$port" =~ ^[0-9]+$ ]] || die "--port muss numerisch sein."
[[ -z "$identity" || -f "$identity" ]] || die "SSH-Schlüssel fehlt: $identity"

mkdir -p "$output_dir"
builder_env=()
[[ -z "$platform" ]] || builder_env+=("DOCKER_DEFAULT_PLATFORM=$platform")
env "${builder_env[@]}" "$BUILDER" "$output_dir" "$components"

artifact="$output_dir/rbf-deployment-$(<"$ROOT_DIR/VERSION").tar.gz"
checksum="$artifact.sha256"
[[ -f "$artifact" ]] || die "Builder hat kein Artifact erzeugt: $artifact"
(cd "$(dirname "$artifact")" && sha256sum "$(basename "$artifact")" > "$(basename "$checksum")")

ssh_args=(-p "$port" -o BatchMode=yes -o StrictHostKeyChecking=yes)
scp_args=(-P "$port" -o BatchMode=yes -o StrictHostKeyChecking=yes)
if [[ -n "$identity" ]]; then
  ssh_args+=(-i "$identity")
  scp_args+=(-i "$identity")
fi

quoted_remote_dir="$(printf '%q' "$remote_dir")"
ssh "${ssh_args[@]}" "$target" "install -d -m 0750 -- $quoted_remote_dir"
scp "${scp_args[@]}" "$artifact" "$checksum" "$target:$remote_dir/"
echo "Übertragen: $target:$remote_dir/$(basename "$artifact")"
echo "Prüfsumme:  $checksum"
