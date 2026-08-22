# Backup-server quickstart

You configure the backup server once. After the connection is verified, WoSB
automatically creates and uploads a backup every night and before every normal
update. Installing or scheduling the Recovery Tool is **not** required for this
automation.

## One-time setup

1. Open **Staff → Operations → Application backups**.
2. On the website server, run the command shown beside the token field:

   ```bash
   sudo /srv/rbf/current/infrastructure/scripts/services/arm-host-operation.sh prepare_enrollment
   ```

   Paste the printed one-time token, select **Create request**, wait for the
   operation to finish, then select **Download request**.
3. Copy that JSON file into `~/Downloads` on the Ubuntu or Debian backup server.
4. Enter the backup server's reachable IP address or DNS name in the page and
   copy the generated command. Run it as your normal user on the backup server.
   The command downloads the provisioner and checksum matching the deployed
   application release, verifies them,
   and asks for `sudo` once.
5. Upload the generated response JSON in the page. The filename includes the
   enrollment ID, but the page validates its JSON content rather than trusting
   its name. Run the
   `apply_enrollment` token command shown there and paste the new token, compare
   the shown SSH fingerprint with the provisioning output, then select
   **Import and verify response**.
6. Create one manual test backup. A successful upload confirms that nightly and
   pre-update backups can use the same connection.

That is the complete automation setup. The application timer runs daily at
03:15 with a randomized delay of up to 20 minutes, and missed runs are caught up
after boot. Normal updates refuse to activate unless their coordinated backup
succeeds.

## Keep the recovery keys safe

The backup server creates private recovery material under `~/RBF-Recovery`.
Copy that directory to a second encrypted offline location. The website never
receives these private keys.

Use the [Recovery Tool](../../tools/recovery-tool/README.md) only when you want
to list, pull, verify, or restore committed backup sets.
