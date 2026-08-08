# Infrastructure Architecture

## Stable Entry Points

The public commands live in the parent repository:

- `<repo>/deploy.sh --configure` configures the test server; test is the default target.
- `<repo>/deploy.sh --production --configure` explicitly configures production.
- `<repo>/deploy.sh` and `<repo>/update.sh` delegate to the origin transfer;
  `--production` is required for every production run.
- `scripts/diagnostics/debug.sh` follows the same target selection and writes
  redacted output locally at the origin.

The targets inside `infrastructure/` intentionally remain in place. This allows the
internal runtime and recovery workflows to be versioned and invoked from the dispatcher.
All shared scripts live under `infrastructure/scripts/`. `quality/` and
`generation/` are origin/CI-side modules; host and runtime modules are packaged
through an explicit allowlist. Only `deploy.sh` and `update.sh` remain at the root.
Owner-bound helpers in `.agents/scripts/` and `frontend/scripts/` remain with their modules.

### Diagnostic Boundary

The origin collector uses the host, user, port, installation root, and identity from the
selected `.env.origin.test` or `.env.origin.production` profile. Test is active without a
flag; production requires `--production`. It streams the verified remote collector over SSH
to `sudo -n bash` without storing it or raw logs on the target. The remote portion reads only
systemd and Compose logs or service status. Only at the origin are IP addresses, email
addresses, query values, and credentials redacted; the bounded output is written with
restrictive permissions under `.diagnostics/` or an explicit local path.

## Responsibilities

### Internal Host Setup

- `setup.sh`: internal runner for local development and artifact installation;
  not a public root wrapper.
- `scripts/setup/options.sh`: CLI, defaults, and input validation.
- `scripts/setup/workflow.sh`: first-run setup order.
- `scripts/setup/main.sh`: composition root; connects options, host, and Docker.

### Host Provisioning

`scripts/lib/host.sh` is a compatible facade. The implementation is split into:

- `scripts/lib/host/packages.sh`: operating-system packages and Docker.
- `scripts/lib/host/storage.sh`: runtime directories, owners, and permissions.
- `scripts/lib/host/firewall.sh`: UFW rules.
- `scripts/lib/host/tls.sh`: bootstrap and Let's Encrypt certificates.

### Quality and Generation

- `scripts/quality/validate.sh`: complete repository gate.
- `scripts/quality/tests/`: infrastructure, update, and diagnostic contracts.
- `scripts/generation/`: API reference, Java contracts/routes, Build catalog,
  Flyway baseline, and webhook templates.

### Controlled Server Actions

- `scripts/services/update.sh`: root-owned host runner for verified inbox artifacts and local `restart`/`rollback` recovery; normal artifacts continue to be built and transferred at the origin.
- `scripts/services/restart-application.sh`: restarts only API and gateway, waits for readiness, and keeps PostgreSQL online.

### Direct Discord Channel Webhooks

The API container sends selected application events directly to official Discord channel webhook URLs over the outbound network.
