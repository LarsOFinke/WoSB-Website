# Backup-server quickstart

1. Download `provision-rbf-backup-server.sh` and its `.sha256` sidecar from the same signed release as the application.
2. In the application, create and download the enrollment request.
3. Put all three files in `~/Downloads` on the Ubuntu/Debian backup host.
4. Let the admin panel generate the complete provisioning command and run it as the normal operator account; the command uses `sudo` only for the provisioner.
5. Compare the printed `SHA256:...` SSH host-key fingerprint independently.
6. Import `~/Downloads/rbf-backup-enrollment-response.json` into the application and require the complete SFTP write test to pass.
7. Trigger a manual coordinated backup.
8. Store the private files under `~/RBF-Recovery` in a second encrypted offline location.

## Configure routine recovery pulls

On the backup host, use the shared recovery client to create a named profile.
Repeat the command with `--target production` and `--target test` when both
environments have independent backup responses:

```text
rbf-recovery-tool setup --target production \
  --response ~/Downloads/rbf-backup-enrollment-response.json \
  --local-backup-host
rbf-recovery-tool test --target production
rbf-recovery-tool pull --target production
```

The client keeps test and production destinations separate, verifies the live
host key, and performs the Spring/Flyway recovery checks locally after every
pull. The website remains the enrollment authorization surface; it is not
needed for routine catalog, pull or bundle verification operations.

The standard path does not copy private keys between hosts and does not grant shell access to either SFTP account.
