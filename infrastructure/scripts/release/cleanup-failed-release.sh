#!/usr/bin/env bash
set -Eeuo pipefail
die() { echo "[cleanup] $*" >&2; exit 1; }
[[ "$EUID" -eq 0 ]] || die "Das Aufräumen benötigt root-Rechte."
for command in flock python3 realpath systemctl; do command -v "$command" >/dev/null 2>&1 || die "Benötigtes Kommando fehlt: $command"; done
install_root="${RBF_INSTALL_ROOT:-/opt/rbf}"; version=""; assume_yes=false; if_present=false; replace_active=false
while (($#)); do
  case "$1" in
    --version) version="${2:-}"; shift 2 ;;
    --install-root) install_root="${2:-}"; shift 2 ;;
    --yes) assume_yes=true; shift ;;
    --if-present) if_present=true; shift ;;
    --replace-active) replace_active=true; shift ;;
    -h|--help) echo 'Usage: cleanup-failed-release.sh [--version X.Y.Z] [--install-root DIR] [--yes]'; exit 0 ;;
    *) die "Unbekannte Option: $1" ;;
  esac
done
[[ "$install_root" == /* && "$install_root" != / ]] || die "Installationsroot muss absolut sein."
install_root="$(realpath -m "$install_root")"; shared="$install_root/shared"; releases="$install_root/releases"
if [[ ! -d "$releases" || ! -d "$shared/deployments" ]]; then
  [[ "$if_present" == true ]] && { echo "[cleanup] Keine bestehende Release-Verwaltung gefunden; übersprungen."; exit 0; }
  die "Keine Release-Verwaltung unter $install_root gefunden."
fi
install -d -m 0700 "$shared/locks"; exec 9>"$shared/locks/release.lock"; flock 9
current_target="$(readlink -f "$install_root/current" 2>/dev/null || true)"
if [[ "$replace_active" == true ]]; then
  [[ -n "$current_target" && "$current_target" == "$releases/"* && -d "$current_target" ]] \
    || { [[ "$if_present" == true ]] && { echo "[cleanup] Kein aktiver Release gefunden; übersprungen."; exit 0; }; die "Kein sicher ersetzbarer aktiver Release gefunden."; }
  version="$(basename "$current_target")"
  [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "Aktiver Release hat keine gültige Version: $version"
  [[ "$assume_yes" == true ]] || die "--replace-active benötigt --yes."
  echo "[cleanup] Ersetze aktiven Release $version für den angeforderten Deploy."
  systemctl stop rbf-hub.service >/dev/null 2>&1 || true
  rm -f "$install_root/current" "$install_root/.current.next"
  rm -rf -- "$current_target"
  rm -f "$shared/deployments/$version.json" "$shared/deployment-state.json"
  echo "[cleanup] Aktiver Release $version entfernt; Shared-Daten und Environment bleiben erhalten."
  exit 0
fi
if [[ -z "$version" ]]; then
  mapfile -t candidates < <(python3 - "$releases" "$shared/deployments" "$current_target" <<'PY'
import json, sys
from pathlib import Path
releases=Path(sys.argv[1]); deployments=Path(sys.argv[2]); current=Path(sys.argv[3]) if sys.argv[3] else None
for release in sorted(releases.iterdir() if releases.exists() else []):
    if not release.is_dir() or release.name.startswith('.') or (current and release.resolve() == current): continue
    try: state=json.loads((deployments/f'{release.name}.json').read_text()).get('state','')
    except (OSError,ValueError): continue
    if state in {'failed','activating'}: print(release.name)
PY
  )
  ((${#candidates[@]} == 1)) && version="${candidates[0]}"
  if ((${#candidates[@]} > 1)); then printf 'Aufräumbare Releases:\n%s\n' "${candidates[*]}" >&2; read -r -p 'Version: ' version; fi
  if [[ -z "$version" ]]; then
    [[ "$if_present" == true ]] && { echo "[cleanup] Kein fehlgeschlagener Release gefunden; übersprungen."; exit 0; }
    die "Kein aufräumbarer fehlgeschlagener Release gefunden."
  fi
fi
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "Version ist kein gültiges SemVer: $version"
release_dir="$releases/$version"; record="$shared/deployments/$version.json"
[[ -d "$release_dir" && ! -L "$release_dir" ]] || die "Release-Verzeichnis fehlt oder ist unsicher."
[[ -f "$record" && ! -L "$record" ]] || die "Deployment-Metadaten fehlen."
state="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("state",""))' "$record")"
[[ "$state" == failed || "$state" == activating ]] || die "Nur failed/activating darf bereinigt werden (Status: $state)."
[[ "$current_target" != "$release_dir" ]] || die "Sicherheitsabbruch: Release ist aktuell aktiv."
if [[ "$assume_yes" != true ]]; then read -r -p "Release $version entfernen? [j/N]: " answer; case "${answer,,}" in j|ja|y|yes) ;; *) die "Aufräumen abgebrochen." ;; esac; fi
[[ "$(readlink -f "$install_root/.current.next" 2>/dev/null || true)" != "$release_dir" ]] || rm -f "$install_root/.current.next"
rm -rf -- "$release_dir"
python3 -c 'import json,sys; from datetime import datetime,timezone; from pathlib import Path; p=Path(sys.argv[1]); d=json.loads(p.read_text()); d["state"]="failed"; d["cleaned_at"]=datetime.now(timezone.utc).isoformat(); p.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); p.chmod(0o600)' "$record"
echo "[cleanup] Release $version entfernt; Backups, Artefakte und Diagnoselogs bleiben erhalten."
