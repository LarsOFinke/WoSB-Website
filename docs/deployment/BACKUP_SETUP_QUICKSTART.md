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
   keys, installs the Recovery Tool without GitHub, and enables the target-specific
   one-minute synchronization timer. Backups are stored below
   `/backups/wosb/<environment>`.
3. **Website UI:** upload the response JSON created by step 2. Run the displayed
   `apply_enrollment` approval command on the **website server**, paste its
   token, compare the website SSH fingerprint, and import the response.
4. **Backup server:** verify the pinned endpoint, then request and collect one
   fresh backup to validate the enrollment. Published website and update
   exports are collected automatically by the installed per-environment timer:

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

## Optional backup-backup copy via SCP

The durable backup roots live on the backup server and are deliberately owned by
root with mode `0700`. A third host may keep a second copy, but it must connect
to the backup server using an administrative SSH account; the website's
chrooted `rbf-backup-controller-*` accounts can see only `/exports` and must not
be used for this purpose.

If the backup-backup host uses the account `lars-oliver-finke`, grant it
read/traverse access on the backup server. Run these commands **on the backup
server**:

```bash
sudo setfacl -m u:lars-oliver-finke:--x /backups /backups/wosb
for target in test production; do
  sudo setfacl -R -m u:lars-oliver-finke:rX /backups/wosb/"$target"
  sudo setfacl -m d:u:lars-oliver-finke:r-x,d:m::r-x /backups/wosb/"$target"
done
```

The default ACL keeps access available for newly created backup sets. This
grants read-only access to encrypted backup artifacts and manifests; it does
not grant the age identities or Recovery Tool configuration under
`/etc/rbf-recovery-tool`.

From the backup-backup host, verify and copy a target with:

```bash
ssh lars-oliver-finke@<backup-server> \
  'find /backups/wosb/production -maxdepth 1 -type f | head'
scp -r lars-oliver-finke@<backup-server>:/backups/wosb/production .
```

Repeat for `/backups/wosb/test` when required. Keep the second copy encrypted
and restrict its storage and SSH key access. For a complete disaster-recovery
copy, separately protect `/etc/rbf-recovery-tool`, which contains the private
age identities needed to decrypt the bundles; do not expose that directory via
SCP ACLs.

## Updating an older enrollment

Deploy the corrected release to the selected website first. The deployment
reconciles that target's own host and port into `.env`. Then create and import a
fresh enrollment response for that environment. Re-enrollment updates the
endpoint and pinned host key while preserving the environment's existing
private controller key, age identity, and `/backups/wosb/<environment>` data.
Do not edit `profiles.json`, `known_hosts`, or authorized-key files manually.

If only the installed Recovery Tool needs updating, use the versioned helper
from a trusted repository checkout on the backup server:

```bash
sudo ./update-recovery-tool.sh
```

This preserves the target-specific profiles, private keys, enrollment state and
backup data, then reconciles the separate `test` and `production` sync timers.
It does not replace website enrollment; endpoint, host-key, or environment
changes still require a fresh enrollment response.

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

- The **backup server** automatically runs `sync --target` independently for
  test and production every minute. Use `run --target` only when a deliberately
  fresh backup is required.
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
