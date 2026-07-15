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
  if [[ ! -d "$REPO_ROOT/.git" ]]; then
    warn "Kein .git-Verzeichnis gefunden; Quellcode-Update wird übersprungen. Die Datenbankrevision wird trotzdem gegen das gebaute Image geprüft."
    return 0
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
