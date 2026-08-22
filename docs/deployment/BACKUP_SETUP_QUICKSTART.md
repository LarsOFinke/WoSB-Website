# Backup-server quickstart

You configure the backup server once per website environment. After each
connection is verified, WoSB
automatically creates and uploads a backup every night and before every normal
update. Installing or scheduling the Recovery Tool is **not** required for this
automation.

Test and production may use the same physical backup server. Each website
server's existing private `infrastructure/.env` must contain exactly one of:

```dotenv
DEPLOYMENT_ENVIRONMENT=test
DEPLOYMENT_ENVIRONMENT=production
```

The deployment tooling writes this value automatically. Enrollment reads it
from the **website/target server** and derives all backup-server identities; the
operator does not choose a directory or account manually.

## One-time setup

1. Open **Staff → Operations → Application backups**.
2. On the **website/target server**, run the command shown beside the token field:

   ```bash
   sudo /srv/rbf/current/infrastructure/scripts/services/arm-host-operation.sh prepare_enrollment
   ```

   Paste the printed one-time token, select **Create request**, wait for the
   operation to finish, then select **Download request**.
3. Confirm that the page shows the intended `TEST` or `PRODUCTION` target and
   its derived directory. Copy that JSON file into `~/Downloads` on the Ubuntu
   or Debian **backup server**.
4. Enter the backup server's reachable IP address or DNS name in the page and
   copy the generated command. Run it as your normal user on the **backup
   server**. The request contains the provisioner matching the deployed
   application release; the command extracts it, verifies its checksum, and
   asks for `sudo` once. No GitHub release or repository checkout is required.
5. Upload the generated response JSON in the page. The filename includes the
   enrollment ID, but the page validates its JSON content rather than trusting
   its name. Run the
   `apply_enrollment` token command shown there on the **website/target server**
   and paste the new token, compare
   the shown SSH fingerprint with the provisioning output, then select
   **Import and verify response**.
6. Create one manual test backup. A successful upload confirms that nightly and
   pre-update backups can use the same connection. Success means the **backup
   server** independently accepted the set and moved it into
   website-inaccessible storage.

That is the complete automation setup. The application timer runs daily at
03:15 with a randomized delay of up to 20 minutes, and missed runs are caught up
after boot. Normal updates refuse to activate unless their coordinated backup
succeeds.

Repeat the enrollment once from each website server when both environments use
the same backup server. Their resources are deliberately separate:

| Website environment | Upload account | Recovery account | Backup-server storage |
| --- | --- | --- | --- |
| Test | `rbf-backup-test` | `rbf-recovery-test` | `/backups/wosb/test` |
| Production | `rbf-backup-production` | `rbf-recovery-production` | `/backups/wosb/production` |

An enrollment response for one environment is rejected by the other. The
backup server also uses separate SSH rules, ingest and retention units, state
files, read groups, and private recovery-key directories for each target.

## Keep the recovery keys safe

The backup server creates private recovery material under
`~/RBF-Recovery/test` and `~/RBF-Recovery/production`. Copy both directories to
a second encrypted offline location. The website never receives these private
keys.

The website account can submit files only to `/incoming` and read the backup
server's receipts from `/receipts`. It cannot enter `/data`, where committed
sets are root-owned. Validation, commitment, retention, recovery reads, and
deletion are controlled by the backup server.

Run the [Recovery Tool](../../tools/recovery-tool/README.md) on the **backup
server** only when you want to list, pull, verify, or restore committed backup
sets.
