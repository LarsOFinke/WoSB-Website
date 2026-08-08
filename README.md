# Royal Blackwater Fleet v1.1.0

Production-ready fleet operations portal for **World of Sea Battle** using Vue 3,
Spring Boot 4, PostgreSQL, Flyway, NGINX, and artifact-based deployment.

## Architecture at a glance

```text
Browser → NGINX → Spring Boot API → PostgreSQL
```

Spring Security is the sole security boundary. `openapi/source/` is the canonical
authoring source for the external HTTP specification; `openapi/openapi.json` is built
from it deterministically for generators and tooling and generates only immutable
request/response DTOs. Module controllers own their Spring MVC routes and validate those
DTOs directly; services own business logic and transactions, repositories encapsulate
JDBC/JPA and SQL, and mappers form the only conversion boundary between API/module DTOs,
entities, and repository rows. Generic `model`/`contract` runtime layers, central
dispatchers, and operation handlers are not part of the backend architecture. Flyway owns
the schema; the former Python backend has been removed completely.

## Local development

Requirements: Java 21, Maven 3.9+, Node.js 22, npm, and PostgreSQL, or Docker for the
integration tests.

```bash
cp infrastructure/.env.example infrastructure/.env
mvn -f spring-api/pom.xml spring-boot:run
```

In a second terminal:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

## Quality checks

```bash
make test          # fast deterministic checks
make test-full     # complete Java/frontend/infrastructure gate
make validate      # identical to the complete release gate
make check-tree    # clean repository tree
```

A release is considered deliverable only when Maven compilation, Spring and PostgreSQL
integration tests, frontend tests and production build, plus the infrastructure and
recovery contract tests have all passed.

## Build and deploy a release

CI, or a complete build environment, creates a source-free, checksum-protected release
artifact:

```bash
bash ./infrastructure/scripts/release/build-artifact.sh
```

For the origin-to-target-server workflow, the **test server is the safe default target**:

```bash
./deploy.sh
./update.sh
```

Production is selected only explicitly:

```bash
./deploy.sh --production
./update.sh --production
```

The origin transfers the verified artifact and `setup_website.sh` over SSH. On the target
server, `setup_website.sh` verifies the package and starts the atomic installation. Test
and production use separate private origin configurations: `.env.origin.test` and
`.env.origin.production`; templates are `.env.origin.test.example` and
`.env.origin.production.example`.

A new test machine is configured with `./deploy.sh --configure`; a new production machine
only with `./deploy.sh --production --configure`. Later invocations use the selected
profile without private application accounts.

Diagnostics use the same safe target selection: test without a flag, and explicit
`--production` for production.

```bash
./infrastructure/scripts/diagnostics/debug.sh
./infrastructure/scripts/diagnostics/debug.sh --production --area calendar --category http-500 --since 30m
```

Output is redacted on the origin and stored locally under `.diagnostics/`; no persistent
debug files are created on the target system.

The target system needs neither Git nor Maven, npm, or access to package registries. It
verifies the bundle and builds only the minimal runtime containers from the already
compiled Spring Boot JAR and Vue `dist`:

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.1.0.tar.gz \
  --checksum rbf-deployment-1.1.0.tar.gz.sha256 \
  --install-root /srv/rbf \
  --env /secure/rbf.env
```

Alternatively, `sudo ./setup_website.sh` is sufficient; the artifact, checksum,
installation root, environment file, and first-installation confirmation are then
requested in the terminal.

Updates are triggered by a new release artifact:

```bash
sudo ./update.sh --artifact /path/to/rbf-deployment-1.1.0.tar.gz
```

`/tmp/rbf-release` is used only as short-lived transfer staging. Persistent release,
configuration, and data structures live under `/srv/rbf`. An existing installation under
`/opt/rbf` is migrated automatically and fail-closed to `/srv/rbf` during the first
deployment.

Rollback, backup, and restore switch the application, Flyway schema, and persistent files
together in a controlled manner. The release artifact associated with the backup is
included in the encrypted recovery bundle.

## Project structure

```text
spring-api/      Spring Boot, Security, Flyway, MapStruct, and business domains
frontend/        Vue 3, modular UI, localization, and deterministic tests
openapi/         modular OpenAPI sources plus generated compatibility artifact
infrastructure/  Compose plus modular quality, generator, release, and runtime scripts
tests/           language-neutral recovery and infrastructure contract tests
docs/            architecture, development, and operations documentation
.github/         CI, release creation, and deployment promotion
```

## Documentation

- [Architecture](docs/architecture/ARCHITECTURE.md)
- [Quality standards](docs/development/QUALITY_STANDARDS.md)
- [Versioning](docs/development/VERSIONING.md)
- [Development](docs/development/DEVELOPMENT.md)
- [Database and Flyway](docs/development/DATABASE.md)
- [API usage and security](docs/reference/API.md)
- [Tests](docs/development/TESTING.md)
- [Deployment](docs/deployment/DEPLOYMENT.md)
- [Installation](docs/deployment/INSTALLATION.md)
- [Operations](docs/deployment/OPERATIONS.md)
- [Disaster Recovery](docs/deployment/DISASTER_RECOVERY.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)
- [Agent onboarding](.agents/ONBOARDING.md)

## License and notices

See [NOTICE.md](NOTICE.md).
