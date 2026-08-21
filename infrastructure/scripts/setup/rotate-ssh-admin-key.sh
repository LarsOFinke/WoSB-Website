#!/usr/bin/env bash
set -Eeuo pipefail

[[ "$EUID" -eq 0 ]] || { echo "SSH key rotation requires root privileges." >&2; exit 1; }
username="${1:-}"; old_public_key_file="${2:-}"; new_public_key_file="${3:-}"; operation="${4:-}"
[[ "$username" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] || { echo "Invalid SSH admin username." >&2; exit 2; }
[[ "$operation" == add || "$operation" == remove ]] || { echo "Operation must be add or remove." >&2; exit 2; }
[[ -f "$old_public_key_file" && ! -L "$old_public_key_file" ]] || { echo "Old SSH public-key file is missing or a symlink." >&2; exit 2; }
[[ -f "$new_public_key_file" && ! -L "$new_public_key_file" ]] || { echo "New SSH public-key file is missing or a symlink." >&2; exit 2; }

getent passwd "$username" >/dev/null || { echo "SSH admin does not exist: $username" >&2; exit 1; }
home="$(getent passwd "$username" | cut -d: -f6)"
primary_group="$(id -gn "$username")"
ssh_dir="$home/.ssh"; authorized_keys="$ssh_dir/authorized_keys"
[[ "$home" != / && "$home" != /srv/rbf ]] || { echo "Unsafe SSH admin home directory." >&2; exit 1; }
install -d -m 0700 -o "$username" -g "$primary_group" "$ssh_dir"
touch "$authorized_keys"; chmod 0600 "$authorized_keys"; chown "$username:$primary_group" "$authorized_keys"

key_material() { awk 'NF >= 2 { print $1 " " $2; exit }' "$1"; }
old_key="$(key_material "$old_public_key_file")"; new_key="$(key_material "$new_public_key_file")"
[[ "$old_key" =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521))[[:space:]]+[A-Za-z0-9+/=]+$ ]] || { echo "Invalid old SSH public key." >&2; exit 2; }
[[ "$new_key" =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521))[[:space:]]+[A-Za-z0-9+/=]+$ ]] || { echo "Invalid new SSH public key." >&2; exit 2; }
[[ "$old_key" != "$new_key" ]] || { echo "Old and new SSH public keys are identical." >&2; exit 2; }

matches_key() { awk -v wanted="$1" 'NF >= 2 && ($1 " " $2) == wanted { found=1 } END { exit(found ? 0 : 1) }' "$2"; }
temporary="$(mktemp "$ssh_dir/.authorized_keys.rotate.XXXXXX")"
cleanup() { rm -f -- "$temporary"; }
trap cleanup EXIT
if [[ "$operation" == add ]]; then
  matches_key "$old_key" "$authorized_keys" || { echo "The current deployment key is not authorized; refusing rotation." >&2; exit 1; }
  if ! matches_key "$new_key" "$authorized_keys"; then
    cat "$authorized_keys" > "$temporary"
    cat "$new_public_key_file" >> "$temporary"
    install -m 0600 -o "$username" -g "$primary_group" "$temporary" "$authorized_keys"
  fi
else
  matches_key "$new_key" "$authorized_keys" || { echo "The replacement deployment key is not authorized; refusing removal." >&2; exit 1; }
  matches_key "$old_key" "$authorized_keys" || { echo "The old deployment key is already absent."; exit 0; }
  awk -v unwanted="$old_key" 'NF < 2 || ($1 " " $2) != unwanted' "$authorized_keys" > "$temporary"
  install -m 0600 -o "$username" -g "$primary_group" "$temporary" "$authorized_keys"
fi
echo "SSH deployment key ${operation}ed for $username."
