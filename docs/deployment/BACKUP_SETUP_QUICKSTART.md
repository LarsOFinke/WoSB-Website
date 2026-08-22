# Backup-server quickstart

You configure the backup server once. After the connection is verified, WoSB
automatically creates and uploads a backup every night and before every normal
update. Installing or scheduling the Recovery Tool is **not** required for this
automation.

## One-time setup

1. Open **Staff → Operations → Application backups**.
2. On the **website/target server**, run the command shown beside the token field:

   ```bash
   sudo /srv/rbf/current/infrastructure/scripts/services/arm-host-operation.sh prepare_enrollment
   ```

   Paste the printed one-time token, select **Create request**, wait for the
   operation to finish, then select **Download request**.
3. Copy that JSON file into `~/Downloads` on the Ubuntu or Debian backup server.
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

## Keep the recovery keys safe

The backup server creates private recovery material under `~/RBF-Recovery`.
Copy that directory to a second encrypted offline location. The website never
receives these private keys.

The website account can submit files only to `/incoming` and read the backup
server's receipts from `/receipts`. It cannot enter `/data`, where committed
sets are root-owned. Validation, commitment, retention, recovery reads, and
deletion are controlled by the backup server.

Run the [Recovery Tool](../../tools/recovery-tool/README.md) on the **backup
server** only when you want to list, pull, verify, or restore committed backup
sets.
