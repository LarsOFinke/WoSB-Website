#!/usr/bin/env bash
set -Eeuo pipefail

repo_owner() {
  stat -c '%U' "$REPO_ROOT" 2>/dev/null || printf 'root'
}

git_as_owner() {
  local owner
  owner="$(repo_owner)"
  if [[ "$owner" != root && "$owner" != UNKNOWN && -n "$owner" ]] && command -v runuser >/dev/null 2>&1; then
    runuser -u "$owner" -- git -C "$REPO_ROOT" "$@"
  else
    git -c safe.directory="$REPO_ROOT" -C "$REPO_ROOT" "$@"
  fi
}

update_repository() {
  if [[ -n "${ARTIFACT_FILE:-}" ]]; then
    COMMIT_BEFORE="artifact-target"
    COMMIT_AFTER="artifact-pending"
    log "Git-Pull und Zielserver-Build werden übersprungen; Deployment-Artefakt wird verwendet."
    return 0
  fi
  if [[ ! -d "$REPO_ROOT/.git" ]]; then
    die "Kein .git-Verzeichnis und kein Deployment-Artefakt vorhanden. Auf diesem Artifact-Ziel bitte update.sh --artifact FILE verwenden; ein Source-Build ist hier nicht möglich."
  fi

  git_as_owner config core.fileMode false
  COMMIT_BEFORE="$(git_as_owner rev-parse --short HEAD)"

  local dirty
  dirty="$(git_as_owner status --porcelain --untracked-files=no)"
  [[ -z "$dirty" ]] || die "Repository enthält lokale Änderungen. Update abgebrochen, um Datenverlust zu vermeiden."

  if [[ "$SKIP_PULL" == false ]]; then
    log "Repository wird per fast-forward aktualisiert."
    git_as_owner fetch --prune origin
    git_as_owner pull --ff-only
  else
    log "Git-Pull wurde per --skip-pull übersprungen."
  fi
  COMMIT_AFTER="$(git_as_owner rev-parse --short HEAD)"
}
