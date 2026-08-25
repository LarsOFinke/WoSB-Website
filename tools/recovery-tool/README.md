# RBF Recovery Tool

The Recovery Tool runs on the **backup server** and is an operational dashboard
and CLI. Website enrollment and terminal provisioning install its profiles and
private keys; this tool does not import enrollment files or manage setup.

For each `test` or `production` profile it connects outbound to the website,
requests a coordinated encrypted backup, downloads only a complete committed
set, verifies all checksums and recovery proof, stores it below
`/backups/wosb/<environment>`, acknowledges the exact set digest, and applies
the configured retention period.

Useful commands on the **backup server**:

```bash
sudo rbf-recovery-tool targets
sudo rbf-recovery-tool test --target production
sudo rbf-recovery-tool run --target production
sudo rbf-recovery-tool sync --target production
sudo rbf-recovery-tool catalog --target production
sudo rbf-recovery-tool verify /backups/wosb/production/rbf-recovery-....tar.gz.age --target production
```

`run` requests and collects a fresh backup. `sync` collects a pending manual or
pre-update export and safely does nothing when none exists. `test` verifies both
the pinned website SSH host key and actual controller authentication. `catalog`
lists committed sets and `verify` checks one local encrypted bundle. Production
and test profiles, keys, and destinations are independent. The managed backup
server provisioner installs a separate one-minute `sync` timer for each enrolled
target, so website and pre-deployment exports are pulled automatically. The
interactive tool remains available for manual checks and fresh `run` requests.

The manual website flow is deliberately a three-way handshake. First, an
operator arms the exact `backup` host capability on the selected website and
confirms the operation in the website. Second, the website creates and publishes
one target-bound committed export; the Recovery Tool must be run with the same
target (`sync --target test` or `sync --target production`). Third, the tool
verifies that exact manifest and encrypted recovery bundle, then acknowledges its
SHA-256 digest. The website reports success only after that acknowledgement.
Never use a production profile to pull test exports, or the reverse. The website
keeps the pending operation open for the configured controller window
(`BACKUP_PULL_ACK_TIMEOUT_SECONDS`, default 15 minutes). Start `sync` promptly
after confirming the website operation; a 100 MiB production export may take
longer to download and verify than a test export.

Profiles from the former shared-account installation are intentionally treated
as unconfigured. They must not be relabeled as test or production because that
could reuse the wrong private key. Complete a fresh enrollment for the affected
environment after installing this version.

The normal profile is under `/etc/rbf-recovery-tool`; its private age identity
is required for disaster recovery. Back up that directory to a second encrypted
offline medium. Never copy those private keys to the website.

## Updating the installed tool

From a trusted checkout on the backup server, update the installed Recovery Tool
atomically with the repository helper:

```bash
sudo ./update-recovery-tool.sh
```

The helper preserves the target profiles, controller keys, age identities,
enrollment state, and `/backups/wosb/<environment>` data. It reconciles only
the enrolled `test` and `production` targets and keeps their one-minute sync
timers separate. Do not replace the installation by copying files into
`/opt/rbf-recovery-tool` manually.

The shared source supports Python 3.11+, Paramiko, and native `age`. Desktop
wrappers remain useful for offline inspection, but are not required for normal
server automation.
