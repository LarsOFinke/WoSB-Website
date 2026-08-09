# RBF Recovery Tool

The recovery client is a small, target-aware pull and verification tool for the
Spring Boot deployment. It accepts only committed backup sets whose report proves
the PostgreSQL dump passed the current Spring/Flyway recovery preflight. It then
downloads the encrypted bundle atomically, checks every sidecar and verifies the
bundle's manifest, including the exact release artifact.

## Setup

The backup server's `rbf-recovery` account is deliberately loopback-only. Run the
tool on that backup host, or use a separately provisioned read-only recovery
account when an off-host recovery workstation is required.

```text
rbf-recovery-tool setup --target test \
  --response ~/Downloads/rbf-backup-enrollment-response.json \
  --local-backup-host
rbf-recovery-tool setup --target production \
  --response ~/Downloads/rbf-backup-enrollment-response.json \
  --local-backup-host
rbf-recovery-tool targets
rbf-recovery-tool test --target production
rbf-recovery-tool pull --target production
```

The setup command imports the public response, selects the local private age
identity and read-only SSH key from `~/RBF-Recovery` when present, verifies the
live pinned host key, and writes a mode-0600 profile store. Test and production
profiles have separate destination directories and can never overwrite each
other by implicit target switching. `--offline` is available only for an
explicitly deferred host-key check; use `test` before any pull.

The response file is still created by the website enrollment workflow because
that workflow authorizes the upload account and binds the host key. The recovery
tool no longer requires the website for routine pulls, catalog checks or local
bundle verification. The website never receives the private recovery keys.

## Build

The shared Python source runs on Linux and Windows with Python 3.11+,
`paramiko`, and the native `age` tools. Native packaging wrappers are provided
under `tools/linux/recovery-tool/` and `tools/windows/recovery-tool/`; they embed
the platform's `age` and `age-keygen` binaries and emit a SHA-256 sidecar.

