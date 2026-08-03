# GitHub CI/CD

## CI

`.github/workflows/ci.yml` läuft auf Pull Requests und `main`:

- Spring Security API: Java-21-/Maven-Build, MapStruct-Compile-Gate und Security-Vertragstests
- Python-Backend: Ruff, isolierte Regressionstests, Alembic- und v1-Datenmigrations-Lifecycle
- Frontend: `npm ci`, Node-Unit-Tests, Build-Designer-Regression, Locale-Vollständigkeit und Produktionsbuild
- Repository/Infrastruktur: Invarianten, Bash und Compose
- Images: Python-API, Spring Security API und Gateway nach erfolgreichem Push auf `main`

Workflow-Rechte sind standardmäßig auf `contents: read` beschränkt; Concurrency bricht veraltete
CI-Läufe derselben Referenz ab.

`.github/workflows/security.yml` ergänzt dies um OSV-Scans der Lockfiles sowie Trivy-Scans beider
API-Images und des Gateway-Images. High-/Critical-Befunde sind ein Release-Gate. Actions sind auf vollständige
Commit-SHAs gepinnt; Abhängigkeits- oder Image-Updates dürfen diese Prüfungen nicht umgehen.

Empfohlene Branch Protection für `main`: Pull Request, mindestens eine Freigabe und die drei
Pflichtchecks Backend, Frontend sowie Repository/Infrastruktur.

## Release

Ein Tag wie `v1.0.0` startet `.github/workflows/release.yml`. Der Workflow validiert den Stand, erzeugt
ein deterministisches ZIP ohne Runtime-Daten, schreibt SHA-256, lädt das Artefakt hoch und erstellt
einen GitHub Release.

```bash
git tag -a v1.0.0 -m 'Royal Blackwater Fleet v1.0.0'
git push origin v1.0.0
```

## Optionales Produktionsdeployment

`.github/workflows/deploy.yml` ist nur manuell startbar und verwendet das geschützte GitHub-
Environment `production`. Hinterlege dort:

```text
RBF_DEPLOY_HOST
RBF_DEPLOY_PORT
RBF_DEPLOY_USER
RBF_DEPLOY_PATH
RBF_DEPLOY_SSH_KEY
RBF_DEPLOY_KNOWN_HOSTS
```

Der Zielbenutzer benötigt nur SSH-Zugang zum Repository sowie eine eng begrenzte sudo-Regel für
`update.sh`. Der private Schlüssel darf keinen weiteren Serverzugriff erlauben. Das Environment
sollte eine manuelle Freigabe verlangen. Das Deployment führt auf dem Pi den vorhandenen,
backup- und lock-geschützten Updater aus; es dupliziert keine Betriebslogik in GitHub Actions.
# Git-freies Image-Deployment (Prototyp)

Für einen minimalistischen Webseiten-Server kann der Build auf dem Backup-/Release-Host
erfolgen. Der Host erhält anschließend nur ein geprüftes Image-Artefakt per SSH; ein Git-
Checkout und ein lokaler Node-, Maven- oder Python-Build sind für das Update nicht nötig.

## Artefakt bauen

Auf dem getrennten Release-Host mit Docker:

```bash
./infrastructure/scripts/release/build-artifact.sh /srv/rbf-releases
sha256sum /srv/rbf-releases/rbf-deployment-*.tar.gz
```

Das Bundle enthält die fertigen Images für FastAPI, Spring Boot und Gateway sowie ein Manifest
und SHA-256-Prüfsummen. Es enthält keine `.env`, Datenbankdaten oder privaten Backup-Schlüssel.

Das Bundle ist unabhängig vom TLS-Zustand des Webseiten-Servers. Es kann während der
Bootstrap-Phase mit einem selbstsignierten Zertifikat installiert und aktualisiert werden. Ein
später ausgestelltes Let's-Encrypt-Zertifikat wird ausschließlich auf dem Webseiten-Server in den
persistenten Zertifikatspfad synchronisiert und bei zukünftigen Image-Updates automatisch weiter
verwendet.

## Übertragen und aktivieren

Das Artefakt wird über den bereits eingerichteten, gepinnten SSH-Zugang übertragen:

```bash
./infrastructure/scripts/release/transfer-artifact.sh \
  /srv/rbf-releases/rbf-deployment-1.0.0.tar.gz \
  deploy@webserver /srv/rbf-releases/incoming 22
ssh deploy@webserver \
  'sudo /opt/royal-blackwater-fleet/update.sh --artifact /srv/rbf-releases/incoming/rbf-deployment-1.0.0.tar.gz --migrate'
```

Der Zielserver prüft Archivpfade, Manifest und Prüfsummen, lädt die Images mit `docker load`,
führt den bestehenden Vorab-Backup-/Migrations-/Smoke-Test-Ablauf aus und behält die zuvor
laufenden Image-Digests für den automatischen Rollback. Die produktive `.env` bleibt ausschließlich
auf dem Webseiten-Server.

## Webhook-Status

Der Artifact-Modus verwendet denselben Update-Status wie der bestehende Git-Modus. Damit werden
die vorhandenen Outbound-Webhook-Ereignisse `system.update.started` und `system.update.result`
auch für Image-Deployments ausgelöst. Ein eingehender Webhook ist nicht erforderlich und bleibt
bewusst deaktiviert; der SSH-Aufruf ist die autorisierte Aktivierung.

Der Prototyp validiert SHA-256-Prüfsummen. Für den produktiven Ausbau sollte zusätzlich eine
Signatur (z. B. cosign/age detached signature) und eine getrennte Release-Berechtigung ergänzt
werden.
