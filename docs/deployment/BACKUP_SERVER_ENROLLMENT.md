# Backup-server enrollment details

For normal installation, follow the
[three-step quickstart](BACKUP_SETUP_QUICKSTART.md). This page documents what the
generated command does and the security boundary it preserves.

The website and backup server exchange public enrollment JSON files only. The
website server generates and retains its private submission key. The backup
server generates and retains the private age identity and a separate read-only,
loopback-only recovery SSH key.

The downloaded request contains the provisioner from the exact deployed
application artifact and its SHA-256 checksum. The generated command, which runs
on the **backup server**, extracts and verifies that embedded provisioner before
invoking it with `sudo`. Setup therefore does not depend on a separately
published GitHub Release or a repository checkout.

The provisioner:

- validates the request schema and one-time enrollment ID;
- installs OpenSSH and `age` when needed;
- creates locked `rbf-backup` and loopback-only `rbf-recovery` accounts;
- configures chrooted SFTP without shell, forwarding, passwords, or TTY access;
- gives the website account access only to `/incoming` and read-only server
  receipts under `/receipts`, never the committed `/data` store;
- installs a root-owned ingest service that independently re-hashes the upload,
  validates its manifest and recovery preflight, copies it into protected
  storage, and publishes the manifest last;
- creates private recovery material under `~/RBF-Recovery`;
- installs bounded retention for committed backup-set manifests; and
- writes a uniquely named enrollment-response JSON with the public host key,
  fingerprint, and age recipient.

The browser imports the response through a file picker and validates its content;
the filename is never treated as proof that it is a response. When imported,
the application binds it to the active request,
checks the live SSH host key, stores root-owned connection data, enables the
encrypted recovery bundle, and performs an isolated ingress round trip. A
backup run is successful only after the backup server returns an acceptance
receipt bound to the submitted manifest checksum. The website cannot list,
read, replace, or delete committed backup sets.

The trust boundary is deliberately asymmetric:

- **Website server:** creates encrypted sets and submits them; it has no recovery
  private key and no committed-store access.
- **Backup server:** decides whether a set is valid, owns committed files,
  controls retention, and provides loopback-only read access to recovery tools.
- **Local workstation/browser:** transfers public enrollment JSON only and has
  no operational backup privileges.

The optional source CIDR in the advanced settings further limits upload access
when the application server has a fixed address. Retention defaults to 30 days.
For stronger availability isolation against a compromised website flooding the
ingress area, place the backup root on a dedicated filesystem with an
administrator-selected capacity or quota; this is infrastructure sizing and is
not required for integrity isolation.
