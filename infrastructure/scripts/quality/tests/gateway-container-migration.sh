#!/usr/bin/env bash
# Optional real-Docker rehearsal, isolated from deployed Compose projects.
set -Eeuo pipefail
image="${RBF_MIGRATION_TEST_IMAGE:-nginx:1.28.0-alpine}"
docker image inspect "$image" >/dev/null
work="$(mktemp -d)"
project="rbf-migration-test-$$"
other="rbf-migration-unrelated-$$"
cleanup() {
  docker compose -p "$project" -f "$work/new.yml" down --remove-orphans >/dev/null 2>&1 || true
  docker rm -f "$other" >/dev/null 2>&1 || true
  rm -rf "$work"
}
trap cleanup EXIT
# Docker allocates ephemeral host ports so the rehearsal never occupies 80/443.
cat > "$work/old.yml" <<YAML
services:
  gateway:
    image: $image
    ports: ["127.0.0.1::80"]
  retired:
    image: $image
YAML
cat > "$work/new.yml" <<YAML
services:
  gateway:
    image: $image
    command: ["nginx", "-g", "daemon off;", "-e", "/dev/stderr"]
    ports: ["127.0.0.1::80"]
YAML
docker run -d --name "$other" "$image" >/dev/null
docker compose -p "$project" -f "$work/old.yml" up -d >/dev/null
old_gateway="$(docker compose -p "$project" -f "$work/old.yml" ps -q gateway)"
retired="$(docker compose -p "$project" -f "$work/old.yml" ps -q retired)"
# Match the systemd stop/reconcile sequence used by the incoming release.
docker compose -p "$project" -f "$work/new.yml" stop >/dev/null
docker compose -p "$project" -f "$work/new.yml" up -d --no-deps --remove-orphans gateway >/dev/null
new_gateway="$(docker compose -p "$project" -f "$work/new.yml" ps -q gateway)"
[[ -n "$new_gateway" && "$new_gateway" != "$old_gateway" ]]
! docker inspect "$old_gateway" >/dev/null 2>&1
! docker inspect "$retired" >/dev/null 2>&1
[[ "$(docker inspect --format '{{.State.Running}}' "$other")" == true ]]
port="$(docker compose -p "$project" -f "$work/new.yml" port gateway 80)"
[[ "$port" == 127.0.0.1:* ]]
curl --fail --silent --retry 10 --retry-connrefused --retry-delay 1 "http://$port/" >/dev/null
printf '[gateway-migration] OK: old gateway replaced, same-project orphan removed, unrelated container retained, loopback HTTP ready\n'
