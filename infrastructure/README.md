# Infrastructure

Dieses Verzeichnis enthält die Spring-only Compose-Laufzeit, TLS-/NGINX-Konfiguration, Host-Control-Runner sowie Release-, Update-, Backup- und Restore-Skripte.

Die beiden Einstiegspunkte für Deployment liegen bewusst auf Repository-Ebene:
`../deploy.sh` überträgt das geprüfte Release-Artefakt; der interne
`scripts/release/setup_website.sh` installiert es auf dem Zielhost.
`scripts/release/` enthält die internen
Release-Implementierungen, den Artefakt-Verifier und den Release-Rollback.
Der Ursprungstransfer läuft über `../deploy.sh`, Updates über `../update.sh`;
der Zielserver nutzt diesen Wrapper.
Die lokale Origin-Konfiguration liegt in `.env.origin` und wird aus
`.env.origin.example` erstellt.

- `compose.yml`: Source-Build für Entwicklung und Erstkonfiguration.
- `compose.release.yml`: Produktion aus kompiliertem JAR und Frontend-`dist`.
- `scripts/release/`: verifizierte, atomare Artifact-Installation und Rollback.
- `scripts/backup/`: koordinierte PostgreSQL-/Datei-/Recovery-Sicherungen.
- `scripts/migration/`: einmaliges, fail-closed Gate für Bestandsdatenbanken.

Produktionsreleases laufen unter `/opt/rbf/releases/<version>`, gemeinsam genutzte Konfiguration und Daten unter `/opt/rbf/shared`, und `/opt/rbf/current` zeigt atomar auf das aktive Release.
