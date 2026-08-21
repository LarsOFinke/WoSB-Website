# Deployment

## Build once

CI runs the complete Java and frontend suites, creates the executable Spring Boot JAR and Vue `dist`, then packages a source-free release:

```bash
bash ./deploy.sh
```

The resulting `rbf-deployment-<version>.tar.gz` contains compiled artifacts, minimal runtime Dockerfiles, Compose configuration and version-matched operations scripts. Every file is listed with size and SHA-256 in `manifest.json` and `SHA256SUMS`.

From the origin server, the **test server is the default target**. `./deploy.sh`
and `./update.sh` load `.env.origin.test`; production is selected exclusively by the
explicit `--production` flag and loads `.env.origin.production`. The artifact,
checksum, website setup wrapper, and verifier are transferred over SSH to the selected
target server. The same flags are available in CI.

```bash
# Test (default)
./deploy.sh
./update.sh

# Production (always explicit)
./deploy.sh --production
./update.sh --production
```

The target-server bootstrap installs missing Docker/Compose dependencies through the
existing host package path; `--skip-host` disables this explicitly. Both private origin
files are maintained with mode `0600`. Templates: `.env.origin.test.example` and
`.env.origin.production.example`.

Run `deploy.sh` and `update.sh` on the origin machine as a normal user and without
`sudo`. Once the selected profile exists, invocation is non-interactive. Configure test
with `./deploy.sh --configure`; configure production deliberately only with
`./deploy.sh --production --configure`. Before the build, the dispatcher checks key
access and `sudo -n`; incomplete target provisioning therefore fails immediately without
a password prompt.

Deployment identities are never stored below the repository. The configuration dialog uses
`$HOME/.ssh/rbf-deploy-<target>-<user>` by default; a bare name entered at the prompt is
resolved below `$HOME/.ssh`, and repository-local paths are rejected before a key can be
read or generated. Origin profiles contain only the resulting external path, never key
material. The same boundary applies to bootstrap, diagnostics, and build-restore identities.
When `--configure` reads an older profile that points below the repository, it ignores that
legacy value and offers the external target-specific default so the replacement key can be
generated safely.
For a fresh target, the initial SSH account intentionally has no default identity: the new
deployment key cannot authenticate that account until its public key is installed. Leave the
bootstrap identity blank to use the account's SSH configuration, agent, or password, or enter
a separate pre-authorized external key explicitly.

`./infrastructure/scripts/diagnostics/debug.sh` follows the same target selection: test
without a flag, production with `--production`. It uses the dedicated SSH key associated
with that target for read-only target-system diagnostics. Unlike deployment, it streams a
small collector over SSH, creates no file on the target, and stores only bounded, redacted
output locally on the origin. Usage and filters are documented in
[OPERATIONS.md](OPERATIONS.md#logs).

The `./deploy.sh --configure` dialog covers the complete first run. It asks for the target
host, persistent SSH admin and identity, optional initial user and VPS key, port, staging
directory, and artifact. If the dedicated deployment key is missing, the dialog can create
an Ed25519 key with restrictive file permissions. This key intentionally has no passphrase
so later automated updates do not require an interactive secret prompt; protect the origin
machine and its user account accordingly. Initial user and bootstrap identity apply only to
that setup run and are stored in neither `.env.origin.test` nor `.env.origin.production`.
On a genuinely new application installation, the release installer additionally verifies
the generated `SEED_ADMIN_USERNAME`/`SEED_ADMIN_PASSWORD` directly through
`/api/auth/login`. This check is deliberately not repeated on updates because the seed
password is not a password-reset mechanism after initial creation.

On a freshly installed target system, `rbfadmin` may not yet exist. In an interactive run,
the dispatcher then asks once for the existing initial user or accepts
`--bootstrap-user USER`. OpenSSH automatically uses host configuration, the SSH agent, and
standard keys; only when the server offers it does password login remain a fallback. A
specific VPS key can be forced with `--bootstrap-identity-file FILE`; then
`IdentitiesOnly=yes` and `BatchMode=yes` are enabled and there is no password prompt. An
initial VPS account named `root` is used directly; other initial users run the provisioner
through `sudo`. Through this explicitly approved connection, the dispatcher transfers only
the provisioner and public key, creates `rbfadmin`, reloads the verified SSH configuration,
and verifies key-only access. The same `deploy.sh` invocation then continues with build,
transfer, and installation. The initial user is stored in no origin profile and is not used
for later updates.

Examples:

```bash
# VPS with key from ~/.ssh/config or SSH agent
./deploy.sh --bootstrap-user root

# VPS with explicit provider key and guaranteed no password fallback
./deploy.sh --bootstrap-user ubuntu \
  --bootstrap-identity-file ~/.ssh/provider-vps
```

The complete first-run dialogs create the separate host administrator and its key access for
each target:

```bash
# Test
./deploy.sh --configure

# Production
./deploy.sh --production --configure
```

During the production dialog, enter the public DNS name and Let's Encrypt contact email.
The target then generates its fresh database, encryption and bootstrap secrets locally and
writes the private runtime environment with mode `0600`; no production secrets are entered
into or stored in the origin profile. The same run requests the certificate after the API
and gateway are ready. Later deployments reuse that target-local environment automatically.

### Migration from the former `.env.origin`

The old single file is deliberately **not imported automatically**, because a fallback could
accidentally point the new test default at production. If the existing `.env.origin`
describes the production server, migrate it once and deliberately:

```bash
cp .env.origin .env.origin.production
chmod 600 .env.origin.production
cp .env.origin.test.example .env.origin.test
chmod 600 .env.origin.test
# then enter test values in .env.origin.test or use ./deploy.sh --configure
```

The old `.env.origin` can then be removed locally. Public deployment/update entry points no
longer use it as an implicit target profile.

For non-interactive provider access, `--bootstrap-user` and `--bootstrap-identity-file` are
also available. The internal `infrastructure/setup.sh` runner is not a public deployment
entry point.

The account is separate from the application administrator, receives no Docker-group access,
authenticates via `publickey`, and has no password, agent, or port-forwarding access. The
private key remains exclusively with the administrator and is never read or copied by setup.
Before disabling global root/password SSH access, test the new access in a second session.

The origin dispatcher uses `RBF_DEPLOY_USER` and `RBF_DEPLOY_IDENTITY_FILE` from the selected
`.env.origin.test` or `.env.origin.production` profile (file mode `0600`). Without explicit
values, it automatically uses `rbfadmin` and checks the target-specific
`$HOME/.ssh/rbf-deploy-<target>-<target-user>` before the legacy
`$HOME/.ssh/<target-user>`. The private key remains exclusively on the origin machine,
outside the source tree. Relative configured names are rooted below `$HOME/.ssh`, while
any resolved repository path fails closed. All SSH/SCP calls run with `BatchMode=yes` and
`IdentitiesOnly=yes`; a missing or incorrect key therefore fails immediately rather than
asking for a password. Before switching the dispatcher, verify access in a second session:

```bash
ssh -o IdentitiesOnly=yes -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no -i ~/.ssh/rbf-deploy-production-rbfadmin rbfadmin@target true
```

## Install atomically

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.0.0.tar.gz \
  --checksum rbf-deployment-1.0.0.tar.gz.sha256 \
  --install-root /srv/rbf \
  --env /secure/rbf.env
```

Before transfer, the origin dispatcher automatically performs cleanup only for failed or
incomplete releases. The active release is never removed before the backup; redeploying the
same already-active version is therefore rejected safely. `/srv/rbf/shared`, including
environment, data, and diagnostics, is preserved.

The installer:

1. verifies outer checksum, safe archive paths and complete inventory;
2. acquires the release lock;
3. uses the verified incoming backup runner against the active release's
   Compose configuration and shared data to create a coordinated
   PostgreSQL/file/recovery backup set before any release switch; activation
   stops if that backup fails;
4. installs `/srv/rbf/releases/<version>`;
5. builds only the small API and gateway runtime images from the JAR and `dist`;
6. switches `/srv/rbf/current` atomically;
7. installs versioned systemd units and runs readiness/smoke tests;
8. writes an activation diagnostic under
   `/srv/rbf/shared/deployments/failed-<version>-<timestamp>.log` and restores
   the previous release where possible on failure.

No Git checkout, Maven, npm or package-registry access is needed on the target host.

The systemd startup deadline covers the complete PostgreSQL initialization,
isolated Flyway migration and Spring readiness sequence. The release installer
must not wrap that sequence in a shorter timeout: first activation on a small VPS
can legitimately take several minutes even when every bounded readiness check is
making progress.

The origin dispatcher does not pass `--skip-backup` or `--no-backup` for normal
updates. The target installer therefore invokes the coordinated backup before
the atomic release switch. Using the incoming runner allows a release to repair
backup orchestration defects in its predecessor without mutating that immutable
active release. On a genuinely empty target, `setup_website.sh`
automatically marks the run as a first installation without a backup; if
release data or an active installation is present, it fails closed and keeps
the backup requirement. `--skip-backup` remains an explicit emergency/operator
override and is not part of the origin update path. Direct target-side artifact
activation is not supported; use `./deploy.sh` for a new transfer and
`./update.sh` for every subsequent release.

Existing hosts using the former `/opt/rbf` structure are migrated automatically by the
installer during the first deployment. The stack is stopped in a controlled manner, the
complete release/shared structure is moved to `/srv/rbf`, and systemd is relinked. The
installer stops if both roots exist at the same time or `current` does not point to a release.
Afterward, artifacts are staged only under `/tmp/rbf-release`.

## Promotion

Build each release once. Promote the same checksummed artifact from CI to staging and production. Do not rebuild per environment. Environment-specific values remain in `/srv/rbf/shared/.env`.

## Rollback

```bash
sudo /srv/rbf/current/infrastructure/scripts/release/rollback-release.sh
```

Rollback restores the previous application release; the coordinated backup
artifacts remain available for the explicit database/file restore path.
