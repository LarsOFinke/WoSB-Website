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
and test profiles, keys, and destinations are independent. Automatic timers are
intentionally not managed by this tool.

Profiles from the former shared-account installation are intentionally treated
as unconfigured. They must not be relabeled as test or production because that
could reuse the wrong private key. Complete a fresh enrollment for the affected
environment after installing this version.

The normal profile is under `/etc/rbf-recovery-tool`; its private age identity
is required for disaster recovery. Back up that directory to a second encrypted
offline medium. Never copy those private keys to the website.

The shared source supports Python 3.11+, Paramiko, and native `age`. Desktop
wrappers remain useful for offline inspection, but are not required for normal
server automation.
