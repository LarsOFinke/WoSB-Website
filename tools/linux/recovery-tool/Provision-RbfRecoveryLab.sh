#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  echo "Usage: Provision-RbfRecoveryLab.sh --user <linux-user>" >&2
}

target_user=""
while (($#)); do
  case "$1" in
    --user) target_user="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

[[ "$EUID" -eq 0 ]] || { echo "Dieses Skript benötigt administrative Rechte." >&2; exit 1; }
[[ -n "$target_user" ]] || { usage; exit 2; }
id "$target_user" >/dev/null 2>&1 || { echo "Benutzer existiert nicht: $target_user" >&2; exit 1; }

. /etc/os-release
[[ "${ID:-}" == "ubuntu" ]] || {
  echo "Die automatische Docker-Provisionierung unterstützt derzeit ausschließlich Ubuntu." >&2
  exit 1
}

for package in docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc; do
  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
    echo "Konfliktpaket erkannt: $package. Es wird aus Sicherheitsgründen nicht automatisch entfernt." >&2
    exit 1
  fi
done

had_rootful=false
if systemctl is-active --quiet docker.service 2>/dev/null || [[ -S /var/run/docker.sock ]]; then
  had_rootful=true
fi

apt-get update
apt-get install -y ca-certificates curl uidmap dbus-user-session slirp4netns
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
apt-get install -y \
  docker-ce docker-ce-cli containerd.io docker-buildx-plugin \
  docker-compose-plugin docker-ce-rootless-extras

allocate_subid() {
  local file="$1" user="$2"
  grep -q "^${user}:" "$file" && return 0
  local start
  start="$(python3 - "$file" <<'PY'
from pathlib import Path
import sys
ranges=[]
path=Path(sys.argv[1])
if path.exists():
    for line in path.read_text().splitlines():
        fields=line.split(":")
        if len(fields)==3:
            try:
                start=int(fields[1]); count=int(fields[2])
            except ValueError:
                continue
            ranges.append((start,start+count-1))
candidate=100000
while any(not (candidate+65535 < lo or candidate > hi) for lo,hi in ranges):
    candidate += 65536
print(candidate)
PY
)"
  printf '%s:%s:65536\n' "$user" "$start" >> "$file"
}
allocate_subid /etc/subuid "$target_user"
allocate_subid /etc/subgid "$target_user"
loginctl enable-linger "$target_user"

if [[ "$had_rootful" == false ]]; then
  systemctl disable --now docker.service docker.socket containerd.service >/dev/null 2>&1 || true
else
  echo "Hinweis: Ein vorhandener rootful Docker-Daemon wurde nicht verändert."
fi

echo "Docker-Pakete und Rootless-Voraussetzungen wurden eingerichtet."
echo "Führe jetzt als $target_user das unprivilegierte Setup-Skript aus."
