# Deployment

## Build once

CI runs the complete Java and frontend suites, creates the executable Spring Boot JAR and Vue `dist`, then packages a source-free release:

```bash
bash ./deploy.sh
```

The resulting `rbf-deployment-<version>.tar.gz` contains compiled artifacts, minimal runtime Dockerfiles, Compose configuration and version-matched operations scripts. Every file is listed with size and SHA-256 in `manifest.json` and `SHA256SUMS`.

Vom Ursprungsserver aus kann der Transfer interaktiv mit `./deploy.sh`
gestartet werden. Dabei werden Artefakt, Prüfsumme, der Website-Setup-Wrapper
und der Verifier per SSH zum Webseitenserver übertragen; dort übernimmt der
Wrapper die Zielserver-Installation. Für CI stehen entsprechende
Flags zur Verfügung.
Der Zielserver-Bootstrap installiert fehlende Docker-/Compose-Abhängigkeiten
über den bestehenden Host-Paketpfad; `--skip-host` deaktiviert dies explizit.
Die erste interaktive Ausführung legt dafür `.env.origin` (chmod 600) an.
Spätere `deploy`-/`update`-Aufrufe laden diese Konfiguration automatisch;
Flags überschreiben einzelne Werte.

Für die getrennte Host-Administration kann das Setup einen eigenen
Schlüsselzugang anlegen:

```bash
sudo ./setup.sh \
  --ssh-admin-username rbfadmin \
  --ssh-admin-public-key-file /secure/operator/rbfadmin.pub
```

Der Account ist vom Anwendungsadministrator getrennt, erhält keinen
Docker-Gruppenzugriff, wird per `publickey` authentifiziert und hat keinen
Passwort-, Agent- oder Port-Forwarding-Zugriff. Der private Schlüssel bleibt
ausschließlich beim Administrator und wird nie vom Setup gelesen oder kopiert.
Vor einer öffentlichen SSH-Freigabe muss der neue Zugang in einer zweiten
Sitzung getestet werden; erst danach dürfen globale Root-/Passwort-SSH-Zugänge
deaktiviert werden.

## Install atomically

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.0.0.tar.gz \
  --checksum rbf-deployment-1.0.0.tar.gz.sha256 \
  --install-root /srv/rbf \
  --env /secure/rbf.env
```

Der Ursprungs-Dispatcher führt vor der Übertragung automatisch einen Cleanup-Lauf
nur für fehlgeschlagene oder unvollständige Releases aus. Der aktive Release wird
niemals vor dem Backup entfernt; ein erneuter Deploy derselben bereits aktiven
Versionsnummer wird daher sicher abgelehnt. `/srv/rbf/shared` mit Environment,
Daten und Diagnosen bleibt erhalten.

Der Installer:

1. verifies outer checksum, safe archive paths and complete inventory;
2. acquires the release lock;
3. creates a coordinated PostgreSQL/file/recovery backup set from the active
   release before any release switch; activation stops if that backup fails;
4. installs `/srv/rbf/releases/<version>`;
5. builds only the small API and gateway runtime images from the JAR and `dist`;
6. switches `/srv/rbf/current` atomically;
7. installs versioned systemd units and runs readiness/smoke tests;
8. writes an activation diagnostic under
   `/srv/rbf/shared/deployments/failed-<version>-<timestamp>.log` and restores
   the previous release where possible on failure.

No Git checkout, Maven, npm or package-registry access is needed on the target host.

The origin dispatcher does not pass `--skip-backup` or `--no-backup` for normal
updates. The target installer therefore invokes the coordinated backup before
the atomic release switch. On a genuinely empty target, `setup_website.sh`
automatically marks the run as a first installation without a backup; if
release data or an active installation is present, it fails closed and keeps
the backup requirement. `--skip-backup` remains an explicit emergency/operator
override and is not part of the origin update path. Direct target-side artifact
activation is not supported; use `./deploy.sh` for a new transfer and
`./update.sh` for every subsequent release.

Bestehende Hosts aus der früheren `/opt/rbf`-Struktur werden beim ersten
Deployment mit dem Installer automatisch migriert. Dabei wird der Stack
kontrolliert gestoppt, die vollständige Release-/Shared-Struktur nach `/srv/rbf`
verschoben und systemd neu verlinkt. Der Installer bricht ab, wenn beide Roots
gleichzeitig existieren oder `current` kein Release zeigt. Danach werden
Artefakte nur noch unter `/tmp/rbf-release` gestaged.

## Promotion

Build each release once. Promote the same checksummed artifact from CI to staging and production. Do not rebuild per environment. Environment-specific values remain in `/srv/rbf/shared/.env`.

## Rollback

```bash
sudo /srv/rbf/current/infrastructure/scripts/release/rollback-release.sh
```

Rollback restores the previous application release; the coordinated backup
artifacts remain available for the explicit database/file restore path.
