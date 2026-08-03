#!/usr/bin/env bash
set -Eeuo pipefail

artifact_prepare() {
  [[ -n "${ARTIFACT_FILE:-}" ]] || return 0
  [[ -f "$ARTIFACT_FILE" ]] || die "Deployment-Artefakt nicht gefunden: $ARTIFACT_FILE"
  require_command sha256sum
  require_command tar

  local artifact_dir="$RUN_DIR/artifact"
  rm -rf "$artifact_dir"
  install -d -m 0700 "$artifact_dir"
  if tar -tzf "$ARTIFACT_FILE" | awk 'BEGIN { bad=0 } index($0, "/") == 1 || $0 ~ /(^|\/)\.\.(\/|$)/ { bad=1 } END { exit bad }'; then
    tar -xzf "$ARTIFACT_FILE" -C "$artifact_dir"
  else
    die "Deployment-Artefakt enthält einen unsicheren Archivpfad."
  fi
  [[ -f "$artifact_dir/manifest.json" && -f "$artifact_dir/images.tar" && -f "$artifact_dir/SHA256SUMS" ]] \
    || die "Deployment-Artefakt ist unvollständig (manifest.json, images.tar oder SHA256SUMS fehlt)."
  (cd "$artifact_dir" && sha256sum --check SHA256SUMS) \
    || die "Prüfsummen des Deployment-Artefakts stimmen nicht."
  [[ -f "$artifact_dir/contracts/recovery/contract.py" ]] \
    || die "Deployment-Artefakt enthält keinen portablen Recovery-Vertrag."
  [[ -d "$artifact_dir/backend/migrations/versions" ]] \
    || die "Deployment-Artefakt enthält keinen Alembic-Migrationsgraphen."
  [[ -d "$artifact_dir/backend/config" ]] \
    || die "Deployment-Artefakt enthält keine Backend-Konfiguration für Recovery."
  export RBF_ARTIFACT_ROOT="$artifact_dir"

  local values=()
  mapfile -d '' -t values < <(ARTIFACT_MANIFEST="$artifact_dir/manifest.json" python3 - <<'PY'
import json
import os
import re
from pathlib import Path

payload = json.loads(Path(os.environ["ARTIFACT_MANIFEST"]).read_text(encoding="utf-8"))
if payload.get("schema_version") != 1 or payload.get("kind") != "rbf-deployment-artifact":
    raise SystemExit("Unsupported deployment artifact manifest.")
version = str(payload.get("version") or "").strip()
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", version):
    raise SystemExit("Invalid deployment artifact version.")
images = payload.get("images")
components = payload.get("components")
expected = ("api", "secure-api", "gateway")
if not isinstance(components, list) or not components or any(item not in expected for item in components) or len(set(components)) != len(components):
    raise SystemExit("Deployment artifact contains an invalid component list.")
if not isinstance(images, dict) or set(images) != set(components):
    raise SystemExit("Deployment artifact images must match its component list.")
for service in components:
    image = str(images[service] or "")
    if not re.fullmatch(r"[A-Za-z0-9./_-]+:[A-Za-z0-9._-]+", image):
        raise SystemExit(f"Invalid image reference for {service}.")
print(version, end="\0")
for service in expected:
    print(str(images.get(service) or ""), end="\0")
print(",".join(components), end="\0")
PY
  )
  [[ "${#values[@]}" -eq 5 ]] || die "Deployment-Artefakt-Manifest konnte nicht validiert werden."
  ARTIFACT_VERSION="${values[0]}"
  local artifact_api="${values[1]}" artifact_secure="${values[2]}" artifact_gateway="${values[3]}"
  local artifact_components="${values[4]}"
  if [[ "${UPDATE_COMPONENTS:-api,secure-api,gateway}" != "api,secure-api,gateway" && "${UPDATE_COMPONENTS}" != "$artifact_components" ]]; then
    die "--components stimmt nicht mit den Komponenten des Deployment-Artefakts überein."
  fi
  UPDATE_COMPONENTS="$artifact_components"
  [[ -n "$artifact_api" ]] || artifact_api="${API_IMAGE_TAG_BEFORE:-}"
  [[ -n "$artifact_secure" ]] || artifact_secure="${SECURE_API_IMAGE_TAG_BEFORE:-}"
  [[ -n "$artifact_gateway" ]] || artifact_gateway="${GATEWAY_IMAGE_TAG_BEFORE:-}"
  [[ -n "$artifact_api" && -n "$artifact_secure" && -n "$artifact_gateway" ]] || die "Für nicht aktualisierte Komponenten ist kein laufendes Image verfügbar."
  export RBF_API_IMAGE="$artifact_api" RBF_SECURE_API_IMAGE="$artifact_secure" RBF_GATEWAY_IMAGE="$artifact_gateway" UPDATE_COMPONENTS
  log "Lade prüfsummenverifizierte Deployment-Images aus Release ${ARTIFACT_VERSION}."
  docker load --input "$artifact_dir/images.tar" >/dev/null
  COMMIT_AFTER="artifact:${ARTIFACT_VERSION}"
  export ARTIFACT_VERSION COMMIT_AFTER
}
