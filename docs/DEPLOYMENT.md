# GitHub CI/CD

## CI

`.github/workflows/ci.yml` läuft auf Pull Requests und `main`:

- Backend: Ruff, isolierte Regressionstests, Alembic- und v1-Datenmigrations-Lifecycle
- Frontend: `npm ci`, Node-Unit-Tests, Build-Designer-Regression, Locale-Vollständigkeit und Produktionsbuild
- Repository/Infrastruktur: Invarianten, Bash und Compose
- Images: API und Gateway nach erfolgreichem Push auf `main`

Workflow-Rechte sind standardmäßig auf `contents: read` beschränkt; Concurrency bricht veraltete
CI-Läufe derselben Referenz ab.

`.github/workflows/security.yml` ergänzt dies um OSV-Scans der Lockfiles sowie Trivy-Scans der API-
und Gateway-Images. High-/Critical-Befunde sind ein Release-Gate. Actions sind auf vollständige
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
