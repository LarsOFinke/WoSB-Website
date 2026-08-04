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

## Install atomically

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.0.0.tar.gz \
  --checksum rbf-deployment-1.0.0.tar.gz.sha256 \
  --install-root /opt/rbf \
  --env /secure/rbf.env
```

Der Ursprungs-Dispatcher führt vor der Übertragung automatisch einen Cleanup-Lauf
für fehlgeschlagene oder bewusst zu ersetzende Releases aus. Dadurch darf beim
Deploy derselben Versionsnummer der bisher aktive Release entfernt und sauber
neu installiert werden; `/opt/rbf/shared` mit Environment, Daten und Diagnosen
bleibt erhalten.

Der Installer:

1. verifies outer checksum, safe archive paths and complete inventory;
2. acquires the release lock;
3. uses the current transition policy: coordinated application backups are
   currently skipped by the origin dispatcher; the backup scripts remain
   available for a separately planned recovery rollout;
4. installs `/opt/rbf/releases/<version>`;
5. builds only the small API and gateway runtime images from the JAR and `dist`;
6. switches `/opt/rbf/current` atomically;
7. installs versioned systemd units and runs readiness/smoke tests;
8. writes an activation diagnostic under
   `/opt/rbf/shared/deployments/failed-<version>-<timestamp>.log` and restores
   the previous release where possible on failure.

No Git checkout, Maven, npm or package-registry access is needed on the target host.

The origin dispatcher passes `--skip-backup --no-backup` deliberately during this
transition. `--no-backup` is safe there because the cleanup step has already
removed the active release while preserving shared state. Direct target-side
artifact activation is not supported; use `./deploy.sh` for a new transfer and
`./update.sh` for every subsequent release.

## Promotion

Build each release once. Promote the same checksummed artifact from CI to staging and production. Do not rebuild per environment. Environment-specific values remain in `/opt/rbf/shared/.env`.

## Rollback

```bash
sudo /opt/rbf/current/infrastructure/scripts/release/rollback-release.sh
```

Rollback restores the previous application release. Database restore remains a
separate, explicitly supervised operation until the coordinated backup manifest
path is re-enabled.
