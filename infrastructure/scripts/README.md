# Infrastruktur-Skripte

Die Skripte sind nach Betriebsgrenzen organisiert. Einstiegspunkte bleiben
stabil; interne Helfer werden nicht direkt aus systemd oder der CI aufgerufen.

## Einstiegspunkte

- `../../deploy.sh --configure` ist der öffentliche First-Run-Aufruf.
- `../../deploy.sh` und `../../update.sh` delegieren an `release/deploy-from-origin.sh`.
  Beide Namen bleiben als kompatible Benutzerverträge erhalten.
- `../setup.sh` delegiert intern an `setup/` und wird nur von lokalen
  Entwicklungs- und Artefaktabläufen aufgerufen.
- `release/build-artifact.sh` baut und validiert das kompilierte Deployment-Artefakt.
- `services/boot.sh`, `services/start.sh`, `services/stop.sh` und
  `services/systemd-stop.sh` bilden den Container-Lebenszyklus.

## Bereiche

- `backup/`: konsistente Sicherungen, Wiederherstellung, Recovery-Bundles und
  der Admin-Runner. Die `backup_runner_*.py`-Dateien sind Import-Module des
  `backup-admin-runner.py`, auch wenn sie nicht als Shell-Aufrufer erscheinen.
- `checks/`: Preflight-, Host-Sicherheits-, Smoke- und Diagnoseprüfungen.
- `deployment/`: systemd-Installation.
- `lib/`: gemeinsam genutzte Shell-Bibliotheken für Docker, Umgebung, Host,
  Speicher, TLS, JSON und Wartungsstatus.
- `release/`: Artefaktprüfung, Installation, Rollback und TLS-/Host-Vorbereitung.
- `services/`: laufender Anwendungsbetrieb und kontrollierte Admin-Operationen.
- `setup/`: CLI-Optionen und Setup-Orchestrierung.
- `tls/`: Zertifikatserneuerung und Synchronisierung.

## Aufräumprüfung (2026-08-04)

- Alle versionierten Shell-Skripte bestehen `bash -n`.
- Alle versionierten Python-Skripte bestehen `python3 -m compileall`.
- Öffentliche Wrapper (`deploy.sh`, `update.sh`) wurden nicht
  zusammengelegt, weil sie bestehende Betriebsverträge darstellen.
- Manuelle Recovery-Helfer (`merge-encryption-keyring.sh`,
  `verify-recovery.sh`) wurden nicht gelöscht: fehlende Quelltextverweise sind
  bei bewusst manuellen Notfallwerkzeugen kein Beweis für Nichtverwendung.
- `scripts/package_release.py` bleibt erhalten, da der Release-Workflow es
  weiterhin für das zusätzliche Quellarchiv aufruft.
