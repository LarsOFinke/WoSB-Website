# Security Policy

## Supported version

Only the current v1.x line receives security fixes.

## Reporting

Please do not publish security issues as public issues. Use GitHub Private Vulnerability
Reporting or contact the repository owner directly. Describe the affected version,
reproduction steps, impact, and a possible fix.

## Production principles

- `.env` files, credentials, databases, uploads, and backups are never committed.
- PostgreSQL is bound to loopback only; the API is reachable exclusively through NGINX.
- API and migration containers run as unprivileged users and without the Docker socket.
- Admin updates accept only two fixed operations; browser data is never executed as shell arguments.
- GitHub Actions have read-only permissions by default. Production uses a protected `production`
  environment and a dedicated SSH key.
- Host administration can use a separate key-bound `rbfadmin` account. This account is separated
  from private application accounts, has no Docker-group access, and disables password, agent,
  and forwarding access on an account-specific basis.
- Before migration or seeding, the updater creates a complete safety backup.
- Manual remote backups use a separate root-side systemd runner. The API has neither Docker-socket
  access nor read access to the private backup key; SSH host keys are checked strictly against a
  dedicated `known_hosts` file before every connection.
- Local PostgreSQL restores do not accept browser paths or arbitrary filenames. The host catalogs
  only regular, SHA-256-verified dumps; a restore requires the bootstrap admin, exact confirmation,
  and a one-time host token generated with `sudo`. The plaintext token is not persisted in the queue,
  API response, or audit log. Short-lived restore authorizations are also explicitly excluded from
  recovery bundles.
- The frozen recovery tool for Windows and Linux uses one shared codebase, pins SSH host keys, stores
  no passwords, and verifies transport SHA-256, age decryption, archive structure, manifest inventory,
  and every included file. It opens no inbound ports and requires no firewall exception on the backup laptop.

Rotate secrets immediately after any suspected compromise: PostgreSQL, seed admin,
`WEBHOOK_ENCRYPTION_KEYS`, Discord webhooks, SSH deploy key, and TLS credentials where applicable.

## Secret rotation

`sudo ./infrastructure/setup.sh --regenerate-secrets` is an internal source-tree workflow intended
only for an installation that has not yet been initialized. The public first run uses
`./deploy.sh --configure`. For an existing PostgreSQL instance, rotate the database role, `.env`,
and dependent services together during a planned maintenance window; merely overwriting `.env` is
forbidden. Discord webhook keys are rotated as a comma-separated key-ring list: add the new key first,
wait for maintenance re-encryption and webhook tests, create a backup, and only then remove old keys.

## Privacy and retention

Data minimization and deletion periods are security requirements. Technically enforced periods are
listed in `docs/reference/DATA_RETENTION.md`; open findings and responsibilities are documented in
`docs/development/QUALITY_STANDARDS.md` and `docs/reference/DATA_RETENTION.md`.
Query values, proxy chains, and validated registration secrets must not be stored permanently.
Changes to data flows, logging, third parties, or backups require a renewed privacy review.
