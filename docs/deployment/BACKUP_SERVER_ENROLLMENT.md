# Backup-server enrollment details

For normal installation, follow the
[three-step quickstart](BACKUP_SETUP_QUICKSTART.md). This page documents what the
generated command does and the security boundary it preserves.

The website and backup server exchange public JSON files only. The application
host generates and retains its private upload key. The backup server generates
and retains the private age identity and a separate read-only recovery SSH key.

The generated command downloads the provisioner and its checksum from the exact
release used by the deployed application, then verifies the checksum before
invoking the script with `sudo`. This keeps the setup protocol reproducible even
after a newer release is published.

The provisioner:

- validates the request schema and one-time enrollment ID;
- installs OpenSSH and `age` when needed;
- creates locked `rbf-backup` and loopback-only `rbf-recovery` accounts;
- configures chrooted SFTP without shell, forwarding, passwords, or TTY access;
- creates private recovery material under `~/RBF-Recovery`;
- installs bounded retention for committed backup-set manifests; and
- writes a uniquely named enrollment-response JSON with the public host key,
  fingerprint, and age recipient.

The browser imports the response through a file picker and validates its content;
the filename is never treated as proof that it is a response. When imported,
the application binds it to the active request,
checks the live SSH host key, stores root-owned connection data, enables the
encrypted recovery bundle, and performs an upload/rename/download/compare/delete
test. The connection is not shown as ready until that test passes.

The optional source CIDR in the advanced settings further limits upload access
when the application server has a fixed address. Retention defaults to 30 days.
