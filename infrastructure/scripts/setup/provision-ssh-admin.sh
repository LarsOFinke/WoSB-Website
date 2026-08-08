#!/usr/bin/env bash
set -Eeuo pipefail

SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SETUP_DIR/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"

[[ "$EUID" -eq 0 ]] || die "SSH admin provisioning requires root privileges."

username="${1:-}"
public_key_file="${2:-}"
[[ "$username" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] || die "Invalid SSH admin username."
[[ -f "$public_key_file" && ! -L "$public_key_file" ]] || die "SSH public-key file is missing or is a symlink."

require_command getent
require_command useradd
require_command usermod
require_command id
require_command install
require_command sshd
require_command visudo
require_command mktemp
require_command systemctl

public_key="$(tr -d '\r' < "$public_key_file")"
[[ "$public_key" =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521)[[:space:]]+[A-Za-z0-9+/=]+([[:space:]]+[^[:space:]]+)?$ ]] \
  || die "The SSH public-key file does not contain exactly one supported OpenSSH key."

if getent passwd "$username" >/dev/null; then
  existing_home="$(getent passwd "$username" | cut -d: -f6)"
  [[ -n "$existing_home" && "$existing_home" != "/" ]] || die "The existing SSH admin does not have a safe home directory."
  home="$existing_home"
else
  useradd --create-home --shell /bin/bash "$username"
  home="$(getent passwd "$username" | cut -d: -f6)"
fi
usermod --lock "$username"
primary_group="$(id -gn "$username")"

[[ "$home" != "/srv/rbf" && "$home" != "$INFRA_DIR" ]] || die "The SSH admin must not use an application data directory."

ssh_dir="$home/.ssh"
authorized_keys="$ssh_dir/authorized_keys"
install -d -m 0700 -o "$username" -g "$primary_group" "$ssh_dir"
touch "$authorized_keys"
chmod 0600 "$authorized_keys"
chown "$username:$primary_group" "$authorized_keys"
if ! grep -Fqx -- "$public_key" "$authorized_keys"; then
  printf '%s\n' "$public_key" >> "$authorized_keys"
fi

sudoers="/etc/sudoers.d/rbf-ssh-admin-$username"
umask 022
printf '%s ALL=(ALL:ALL) NOPASSWD: ALL\n' "$username" > "$sudoers"
chmod 0440 "$sudoers"
chown root:root "$sudoers"
visudo -cf "$sudoers" >/dev/null || { rm -f "$sudoers"; die "The sudoers configuration is invalid."; }

dropin_dir="/etc/ssh/sshd_config.d"
dropin="$dropin_dir/90-rbf-ssh-admin-$username.conf"
install -d -m 0755 -o root -g root "$dropin_dir"
temporary_dropin="$(mktemp "$dropin_dir/.rbf-ssh-admin.XXXXXX")"
cat > "$temporary_dropin" <<EOF_SSH
# Managed by RBF setup. Password and forwarding access are disabled for this account.
Match User $username
    AuthenticationMethods publickey
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    PubkeyAuthentication yes
    PermitEmptyPasswords no
    AllowAgentForwarding no
    AllowTcpForwarding no
    X11Forwarding no
EOF_SSH
chmod 0644 "$temporary_dropin"
chown root:root "$temporary_dropin"
previous_dropin="$(mktemp)"
had_previous=false
if [[ -e "$dropin" && ! -L "$dropin" ]]; then
  cp --preserve=mode,ownership,timestamps "$dropin" "$previous_dropin"
  had_previous=true
fi
install -m 0644 -o root -g root "$temporary_dropin" "$dropin"
rm -f "$temporary_dropin"
if ! sshd -t; then
  if [[ "$had_previous" == true ]]; then
    install -m 0644 -o root -g root "$previous_dropin" "$dropin"
  else
    rm -f "$dropin"
  fi
  rm -f "$previous_dropin"
  die "The SSHD configuration is invalid; the previous configuration was restored."
fi
rm -f "$previous_dropin"

if ! systemctl reload ssh.service 2>/dev/null && ! systemctl reload sshd.service 2>/dev/null; then
  die "The verified SSH configuration could not be reloaded."
fi

success "SSH administration user configured: $username (key access, no password/forwarding access)."
