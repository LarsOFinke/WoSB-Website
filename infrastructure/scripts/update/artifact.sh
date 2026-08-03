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
expected = ("api", "secure-api", "gateway")
if not isinstance(images, dict) or tuple(images) != expected:
    raise SystemExit("Deployment artifact must define api, secure-api and gateway images.")
for service in expected:
    image = str(images[service] or "")
    if not re.fullmatch(r"[A-Za-z0-9./_-]+:[A-Za-z0-9._-]+", image):
        raise SystemExit(f"Invalid image reference for {service}.")
print(version, end="\0")
for service in expected:
    print(str(images[service]), end="\0")
PY
  )
  [[ "${#values[@]}" -eq 4 ]] || die "Deployment-Artefakt-Manifest konnte nicht validiert werden."
  ARTIFACT_VERSION="${values[0]}"
  export RBF_API_IMAGE="${values[1]}" RBF_SECURE_API_IMAGE="${values[2]}" RBF_GATEWAY_IMAGE="${values[3]}"
  log "Lade prüfsummenverifizierte Deployment-Images aus Release ${ARTIFACT_VERSION}."
  docker load --input "$artifact_dir/images.tar" >/dev/null
  COMMIT_AFTER="artifact:${ARTIFACT_VERSION}"
  export ARTIFACT_VERSION COMMIT_AFTER
}
