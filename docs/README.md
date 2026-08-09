# Documentation

This index is the entry point for development, deployment, and operations. Documents are grouped by
responsibility; the old filenames were deliberately not duplicated as a second source.

## Agent entry point

- [Agent Onboarding](../.agents/ONBOARDING.md) – token-efficient quick start and task navigation
- [Project Cache](../.agents/PROJECT_CACHE.md) – stable system map and known debugging foundation
- [Module Cache](../.agents/MODULE_CACHE.md) – complete quick overview for backend, frontend, and infrastructure modules
- [Debugging Cache](../.agents/DEBUGGING_CACHE.md) – token-efficient symptom navigation
- [`AGENTS.md`](../AGENTS.md) – binding working rules

The `.agents` documents are navigation aids. Binding quality, architecture, security,
privacy, and operations rules remain in the primary documents listed below.

## Fresh setup (two servers)

1. [Install the website server](deployment/INSTALLATION.md)
2. [Set up the backup server through enrollment](deployment/BACKUP_SETUP_QUICKSTART.md)
3. [Go-live checks](deployment/GO_LIVE.md)
4. [Operations and updates](deployment/OPERATIONS.md)
5. [Disaster recovery](deployment/DISASTER_RECOVERY.md)

The [RBF Recovery Tool](../tools/recovery-tool/README.md) provides the target-aware
test/production pull, catalog and bundle-verification workflow used after enrollment.

The workflow is designed for a fresh website server and a separate backup/recovery server.
The installation guide contains prerequisites, safe defaults, smoke tests, and expected results.

## Architecture and security

- [Architecture](architecture/ARCHITECTURE.md)
- [Module catalog](architecture/MODULE_CATALOG.md)
- [Backup architecture](architecture/BACKUP_ARCHITECTURE.md)
- [Container security and isolation](architecture/CONTAINER_SECURITY.md)

## Development and quality gates

- [Development](development/DEVELOPMENT.md)
- [Tests](development/TESTING.md)
- [Database and migrations](development/DATABASE.md)
- [Quality standards](development/QUALITY_STANDARDS.md)
- [JSON sources and catalogs](development/JSON_CATALOGS.md)
- [Versioning](development/VERSIONING.md)
- [Technical reviews](development/reviews/) – time-scoped refactoring and verification records

## Deployment and operations

- [CI/CD and deployment](deployment/DEPLOYMENT.md)
- [Operations](deployment/OPERATIONS.md)
- [Backup server enrollment (details)](deployment/BACKUP_SERVER_ENROLLMENT.md)
- [Module-oriented debugging](debugging/MODULE_DEBUGGING.md)

Uptime Kuma is no longer part of the production stack. The historical cause and removal
are documented in the [deployment incident index](debugging/DEPLOYMENT_INCIDENTS.md).

## Reference and integrations

- [Reference documents](reference/)
- [API usage and security](reference/API.md)
- [Generated API endpoint reference](reference/API_ENDPOINTS.md)
- [Outbound webhooks](integrations/outbound-webhooks.md)
- [Webhook templates](integrations/webhook-templates/README.md)
- [In-game screenshot catalog](ingame-screenshots/README.md)

## Maintenance contract

Behavior changes update implementation, tests, and the associated documentation in the same
work step. Changes to topology, module boundaries, gates, or central debugging entry points also
update agent onboarding and the project cache. Ephemeral values such as branch, revision, and file
counts are not copied into docs; obtain them live with `bash .agents/scripts/project-context.sh`.
