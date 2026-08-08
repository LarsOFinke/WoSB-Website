#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"

[[ "$EUID" -eq 0 ]] || die "Installation-root migration requires root privileges."
require_command systemctl
require_command mv
require_command readlink
require_command realpath
require_command install

source_root="${1:-/opt/rbf}"
target_root="${2:-/srv/rbf}"
source_root="$(realpath -m "$source_root")"
target_root="$(realpath -m "$target_root")"
[[ "$source_root" != / && "$target_root" != / ]] || die "Installation root must not be /."
[[ "$source_root" != "$target_root" ]] || die "Source and target roots must differ."
[[ -d "$source_root" ]] || die "Old installation root is missing: $source_root"
[[ ! -e "$target_root" && ! -L "$target_root" ]] || die "Target root already exists: $target_root"
[[ -L "$source_root/current" ]] || die "The old installation has no valid current symlink."
current="$(readlink -f "$source_root/current")"
[[ "$current" == "$source_root/releases/"* ]] || die "current points outside the old release management tree."

was_active=false
if systemctl is-active --quiet rbf-hub.service; then
  was_active=true
  systemctl stop rbf-hub.service
fi

install -d -m 0750 "$(dirname "$target_root")"
mv "$source_root" "$target_root"

RBF_SYSTEMD_INFRA_DIR="$target_root/current/infrastructure" \
  "$target_root/current/infrastructure/scripts/deployment/install-systemd.sh"
if [[ "$was_active" == true ]]; then
  systemctl start rbf-hub.service
fi

success "Installationsroot migriert: $source_root -> $target_root"
