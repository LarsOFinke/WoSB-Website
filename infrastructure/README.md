# Infrastructure

Dieses Verzeichnis enthält die Spring-only Compose-Laufzeit, TLS-/NGINX-Konfiguration, Host-Control-Runner sowie Release-, Update-, Backup- und Restore-Skripte.

- `compose.yml`: Source-Build für Entwicklung und Erstkonfiguration.
- `compose.release.yml`: Produktion aus kompiliertem JAR und Frontend-`dist`.
- `scripts/release/`: verifizierte, atomare Artifact-Installation und Rollback.
- `scripts/backup/`: koordinierte PostgreSQL-/Datei-/Recovery-Sicherungen.
- `scripts/migration/`: einmaliges, fail-closed Gate für Bestandsdatenbanken.

Produktionsreleases laufen unter `/opt/rbf/releases/<version>`, gemeinsam genutzte Konfiguration und Daten unter `/opt/rbf/shared`, und `/opt/rbf/current` zeigt atomar auf das aktive Release.
