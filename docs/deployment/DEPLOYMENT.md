# Deployment

## Build once

CI runs the complete Java and frontend suites, creates the executable Spring Boot JAR and Vue `dist`, then packages a source-free release:

```bash
bash infrastructure/scripts/release/build-artifact.sh
```

The resulting `rbf-deployment-<version>.tar.gz` contains compiled artifacts, minimal runtime Dockerfiles, Compose configuration and version-matched operations scripts. Every file is listed with size and SHA-256 in `manifest.json` and `SHA256SUMS`.

## Install atomically

```bash
sudo infrastructure/scripts/release/install-artifact.sh \
  --artifact rbf-deployment-1.0.0.tar.gz \
  --checksum rbf-deployment-1.0.0.tar.gz.sha256 \
  --install-root /opt/rbf \
  --env /secure/rbf.env
```

The installer:

1. verifies outer checksum, safe archive paths and complete inventory;
2. acquires the release lock;
3. creates a coordinated pre-deployment backup when a release is active;
4. installs `/opt/rbf/releases/<version>`;
5. builds only the small API and gateway runtime images from the JAR and `dist`;
6. switches `/opt/rbf/current` atomically;
7. installs versioned systemd units and runs readiness/smoke tests;
8. restores the previous release and database backup on failure.

No Git checkout, Maven, npm or package-registry access is needed on the target host.

## Promotion

Build each release once. Promote the same checksummed artifact from CI to staging and production. Do not rebuild per environment. Environment-specific values remain in `/opt/rbf/shared/.env`.

## Rollback

```bash
sudo /opt/rbf/current/infrastructure/scripts/release/rollback-release.sh
```

Rollback restores both the previous application release and the coordinated database point recorded for the current deployment. Schema evolution should still use additive expand/contract migrations to minimize restore requirements.
