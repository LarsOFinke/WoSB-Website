# Infrastruktur-Skripte

Die Skripte sind nach Betriebsgrenzen organisiert. Einstiegspunkte bleiben
stabil; interne Helfer werden nicht direkt aus systemd oder der CI aufgerufen.

## Einstiegspunkte

- `../../deploy.sh --configure` richtet den Testserver ein; Test ist Standard.
- `../../deploy.sh --production --configure` richtet Production explizit ein.
- `../../deploy.sh` und `../../update.sh` delegieren an `release/deploy-from-origin.sh`;
  Production erfordert bei jedem Lauf `--production`.
- `diagnostics/debug.sh` folgt derselben Zielauswahl und sammelt begrenzte,
  redigierte Zielsystemdiagnosen ausschließlich am Ursprung.
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
- `diagnostics/`: Origin-Collector, flüchtiger Remote-Collector und lokale
  Redaktion für agententaugliche Betriebsdiagnosen.
- `generation/`: deterministische API-, Java-, Flyway-, Build- und
  Dokumentationsgeneratoren. Veröffentlichte Flyway-Dateien bleiben trotz
  verschobenem Generator unveränderlich.
- `lib/`: gemeinsam genutzte Shell-Bibliotheken für Docker, Umgebung, Host,
  Speicher, TLS, JSON und Wartungsstatus.
- `quality/`: Repository-Audits, Hygiene, Security-Prüfung und das vollständige
  Validierungs-Gate; fokussierte Vertragsprüfungen liegen in `quality/tests/`.
- `release/`: Artefaktbau und -prüfung, Packaging, Origin-Transfer,
  Installation, Rollback und TLS-/Host-Vorbereitung.
- `services/`: laufender Anwendungsbetrieb und kontrollierte Admin-Operationen.
- `setup/`: CLI-Optionen und Setup-Orchestrierung.
- `tls/`: Zertifikatserneuerung und Synchronisierung.

## Ablage- und Ownership-Regel

Im Repository-Root bleiben ausschließlich die öffentlichen Bedienverträge
`deploy.sh` und `update.sh`. Alle gemeinsamen Skripte liegen in diesem Baum und
werden nach Verantwortung einem Modul zugeordnet; ein neues top-level `scripts/`
ist unzulässig. `.agents/scripts/` und `frontend/scripts/` sind eng an ihre
jeweiligen Eigentümermodule gebunden und keine allgemeinen Skriptsammlungen.

Die gemeinsame Ablage bedeutet nicht, dass jedes Modul Produktionsbestandteil
ist. `release/package_deployment_artifact.py` verwendet eine explizite
Runtime-Allowlist. `quality/`, `generation/` und die Packaging-Programme selbst
bleiben auf dem Ursprung beziehungsweise in CI und werden nicht ausgeliefert.

## Aufräumprüfung (2026-08-04)

- Alle versionierten Shell-Skripte bestehen `bash -n`.
- Alle versionierten Python-Skripte bestehen `python3 -m compileall`.
- Öffentliche Wrapper (`deploy.sh`, `update.sh`) wurden nicht
  zusammengelegt, weil sie bestehende Betriebsverträge darstellen.
- Manuelle Recovery-Helfer (`merge-encryption-keyring.sh`,
  `verify-recovery.sh`) wurden nicht gelöscht: fehlende Quelltextverweise sind
  bei bewusst manuellen Notfallwerkzeugen kein Beweis für Nichtverwendung.
- `release/package_release.py` bleibt erhalten, da der Release-Workflow es
  weiterhin für das zusätzliche Quellarchiv aufruft.
