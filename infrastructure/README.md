# Infrastructure

Dieses Verzeichnis enthält die Spring-only Compose-Laufzeit, TLS-/NGINX-Konfiguration, Host-Control-Runner sowie Release-, Update-, Backup- und Restore-Skripte.

Die beiden Einstiegspunkte für Deployment liegen bewusst auf Repository-Ebene:
`../deploy.sh` überträgt das geprüfte Release-Artefakt; der interne
`scripts/release/setup_website.sh` installiert es auf dem Zielhost.
`scripts/release/` enthält die internen
Release-Implementierungen, den Artefakt-Verifier und den Release-Rollback.
Der Ursprungstransfer läuft über `../deploy.sh`, Updates über `../update.sh`;
`../debug.sh` verwendet dieselbe SSH-Verbindung für lesende, begrenzte und lokal
redigierte Diagnosen. Der Zielserver nutzt die versionierten Runtime-Wrapper.
Die lokale Origin-Konfiguration liegt in `.env.origin` und wird aus
`.env.origin.example` erstellt.

- `compose.yml`: Source-Build für Entwicklung und Erstkonfiguration.
- `compose.release.yml`: Produktion aus kompiliertem JAR und Frontend-`dist`.
- `scripts/release/`: verifizierte, atomare Artifact-Installation, Rollback und
  das gezielte Aufräumen fehlgeschlagener, nicht aktiver Releases.
- `scripts/backup/`: koordinierte PostgreSQL-/Datei-/Recovery-Sicherungen.
- `scripts/migration/`: einmaliges, fail-closed Gate für Bestandsdatenbanken.
- `scripts/diagnostics/`: Origin-Sammlung, flüchtiger Remote-Collector und
  Redaktion für agententaugliche Diagnoseausgaben.

Die Alpine-basierten API- und Gateway-Runtimeimages wenden beim Build mit
`apk upgrade --no-cache` die Sicherheitsupdates des gebundenen stabilen
Alpine-Zweigs an. Der Security-Workflow scannt danach beide fertigen Images mit
Trivy und bricht bei reparierbaren HIGH-/CRITICAL-Funden ab.

Produktionsreleases laufen unter `/srv/rbf/releases/<version>`, gemeinsam genutzte Konfiguration und Daten unter `/srv/rbf/shared`, und `/srv/rbf/current` zeigt atomar auf das aktive Release.

Nach einem fehlgeschlagenen Versuch kann derselbe Versionsstand erneut installiert
werden, ohne Backups oder Diagnosen zu löschen:

```bash
sudo /srv/rbf/current/infrastructure/scripts/release/cleanup-failed-release.sh --version 1.0.0
```

Das Skript verweigert aktive Releases sowie Zustände außerhalb von `failed` und
`activating`. Mit `--yes` lässt sich die Bestätigung in automatisierten Abläufen
überspringen.
