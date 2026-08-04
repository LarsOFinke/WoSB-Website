# Assisted backup-server enrollment

The enrollment exchanges public information only. The production host retains its private upload key; the backup host generates and retains the private age identity and a separate read-only recovery SSH key.

## Prepare the backup host

Download these two release assets through a trusted channel:

- `provision-rbf-backup-server.sh`
- `provision-rbf-backup-server.sh.sha256`

Place both in `~/Downloads`. The admin panel generates a complete command that verifies the checksum before invoking the script with `sudo`.

The provisioner:

- validates the request schema and enrollment ID;
- installs OpenSSH and `age` when allowed;
- creates locked `rbf-backup` and loopback-only `rbf-recovery` accounts;
- configures chrooted `internal-sftp` without shell, forwarding, password or TTY access;
- creates the private age identity and read-only recovery key under `~/RBF-Recovery`;
- installs bounded retention for committed backup-set manifests;
- writes `rbf-backup-enrollment-response.json` with host key, fingerprint and public age recipient.

## Complete enrollment

1. In Staff → Operations → Application backups, create and download a request.
2. Copy the request and the provisioner assets to the backup host.
3. Enter host, SSH port, storage path, retention and optional source CIDR in the panel.
4. Copy and execute the generated command.
5. Compare the displayed SSH host-key fingerprint through an independent channel.
6. Import the response file. The application binds it to the active enrollment ID, checks the live host key, stores root-owned connection data and performs an upload/rename/download/compare/delete test.
7. Run a coordinated backup and verify that the backup-set manifest is transferred last as the remote commit marker.

Securely copy `~/RBF-Recovery/rbf-recovery-identity.txt` and the read-only private SSH key to encrypted offline storage. They are never uploaded to the production host.
