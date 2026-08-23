# Backup-controller quickstart

Configure each website environment once. The Recovery Tool runs on the
**backup server** and is the controller: it connects outbound to the website,
requests a backup, downloads and verifies it, stores it below `/backups`, and
acknowledges completion. The website never needs the backup server's address or
an inbound connection to it.

## Before setup — website server

The deployment writes the environment-specific SSH endpoint into the private
`infrastructure/.env`. It must identify the environment and an explicit endpoint
of the **website server**:

```dotenv
DEPLOYMENT_ENVIRONMENT=test
BACKUP_CONTROLLER_WEBSITE_HOST=ssh.test.website.example
BACKUP_CONTROLLER_WEBSITE_SSH_PORT=22
```

Use `test` on the test website and the production SSH endpoint on production.
`BACKUP_CONTROLLER_WEBSITE_HOST` may be a DNS name or address reachable by the
backup server; it is never the backup server's address. It must not be left empty
and is never inferred from `APP_HOSTNAME`, because that name may point to the
production website from both environments. Normal deployments reconcile this
value separately for test and production; manual setup must provide it explicitly.
The origin profiles own these values:

```dotenv
# .env.origin.test
RBF_DEPLOY_BACKUP_CONTROLLER_WEBSITE_HOST=ssh.test.website.example
RBF_DEPLOY_BACKUP_CONTROLLER_WEBSITE_PORT=22

# .env.origin.production
RBF_DEPLOY_BACKUP_CONTROLLER_WEBSITE_HOST=ssh.production.website.example
RBF_DEPLOY_BACKUP_CONTROLLER_WEBSITE_PORT=22
```

When omitted, each profile uses its own `RBF_DEPLOY_HOST` and `RBF_DEPLOY_PORT`.
Every deployment reconciles the selected profile into the corresponding target
server's private `.env`; it never copies the other environment's endpoint.

## One-time setup

For an existing installation, use **Update or replace enrollment** in the website
backup page and repeat these steps for the same environment. The provisioner
updates the managed Recovery Tool in place and keeps existing backup data; do not
delete control files or backup directories manually.

1. **Website UI:** open **Staff → Operations → Application backups**. Run the
   displayed `prepare_enrollment` approval command on the **website server**,
   paste its token, create the request, and download the JSON.
2. **Backup server:** place that request JSON in `~/Downloads`, copy the one
   generated command from the website, and run it as your normal user. It asks
   for `sudo` once. The embedded, checksum-pinned installer creates controller
   keys, installs the Recovery Tool without GitHub, and leaves scheduling under
   explicit operator control. Backups are stored below `/backups/wosb/<environment>`.
3. **Website UI:** upload the response JSON created by step 2. Run the displayed
   `apply_enrollment` approval command on the **website server**, paste its
   token, compare the website SSH fingerprint, and import the response.
4. **Backup server:** verify the pinned endpoint, then request and collect one
   fresh backup (automatic timers are intentionally disabled):

   ```bash
   sudo rbf-recovery-tool targets
   sudo rbf-recovery-tool test --target production
   sudo rbf-recovery-tool run --target production
   ```

   Replace `production` with `test` for the test environment.
5. **Website UI:** confirm that the operation and artifact status succeeded. If
   a backup is started from the website UI instead, run `sync --target <environment>`
   on the backup server while the website waits for its acknowledgement.

## Test and production on one backup server

Enroll both website servers separately. Their identities and storage never
overlap:

| Environment | Website SFTP identity | Backup-server storage |
| --- | --- | --- |
| Test | `rbf-backup-controller-test` | `/backups/wosb/test` |
| Production | `rbf-backup-controller-production` | `/backups/wosb/production` |

Each environment also has separate SSH keys, age identity, profile, service,
enrollment state, and retention setting. Responses
are bound to the request and environment, so importing one into the other is
rejected.

## Updating an older enrollment

Deploy the corrected release to the selected website first. The deployment
reconciles that target's own host and port into `.env`. Then create and import a
fresh enrollment response for that environment. Re-enrollment updates the
endpoint and pinned host key while preserving the environment's existing
private controller key, age identity, and `/backups/wosb/<environment>` data.
Do not edit `profiles.json`, `known_hosts`, or authorized-key files manually.

Verify each side independently:

```bash
# Website/target server
sudo getent passwd rbf-backup-controller-test
sudo sshd -t

# Backup server
sudo rbf-recovery-tool targets
sudo rbf-recovery-tool test --target test
sudo rbf-recovery-tool run --target test
```

## Normal operation

- The **backup server** is operated manually for now. Use `run --target` when a
  fresh backup is required and `sync --target` to collect an already-published
  export.
- A normal website update always creates a verified local backup first. It then
  attempts a remote controller acknowledgement; activation continues if the
  controller is temporarily unavailable unless
  `BACKUP_REQUIRE_PULL_ACK_BEFORE_UPDATE=true` is configured.
- The website exports are root-owned and read-only to the SFTP controller. The
  controller can write only requests and acknowledgements.
- Retention is enforced on the backup server. Keep a second encrypted offline
  copy of `/etc/rbf-recovery-tool` because it contains the private age keys.

For troubleshooting and protocol details, see
[Backup-server enrollment](BACKUP_SERVER_ENROLLMENT.md).
