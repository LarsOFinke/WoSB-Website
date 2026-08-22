# RBF Recovery Tool

> This tool is optional during backup-server setup. WoSB itself performs the
> nightly and pre-update uploads after the one-time enrollment. Install this
> client on the backup server when you need to inspect, download,
> verify, or restore those committed backup sets.

The recovery client is a small, target-aware pull and verification tool for the
Spring Boot deployment. It accepts only committed backup sets whose report proves
the PostgreSQL dump passed the current Spring/Flyway recovery preflight. It then
downloads the encrypted bundle atomically, checks every sidecar and verifies the
bundle's manifest, including the exact release artifact.

Strategy planner recovery needs no separate opt-in: strategy documents and their
ship/build/guide references are part of the complete PostgreSQL dump, while chart
backgrounds are stored under the fully archived `uploads/` tree. Pull and verify
the committed recovery bundle as one unit; restoring only one of those artifacts
would leave the strategy boundary incomplete and is intentionally unsupported by
the disaster-recovery workflow.

## Optional recovery-workstation setup

The backup server's environment-specific `rbf-recovery-test` and
`rbf-recovery-production` accounts are deliberately loopback-only. Run the tool
on that backup host, or use a separately provisioned read-only recovery account
when an off-host recovery workstation is required.

Run these commands on the **backup server**:

```text
rbf-recovery-tool setup --target test --local-backup-host
rbf-recovery-tool setup --target production --local-backup-host
rbf-recovery-tool targets
rbf-recovery-tool test --target production
rbf-recovery-tool pull --target production
```

Setup discovers a single valid response in `~/Downloads` by its JSON content,
not its filename. If more than one response exists, use
`--response /path/to/file.json` to select the intended target explicitly.
The GUI's **Import enrollment response…** button and the website enrollment page
both use a file picker and apply the same content validation. Selecting a request
file explains that provisioning must run first.

The setup command imports the public response, requires its environment to
match `--target`, selects the local private age identity and read-only SSH key
from `~/RBF-Recovery/<target>` when present, verifies the
live pinned host key, and writes a mode-0600 profile store. Test and production
profiles have separate destination directories and can never overwrite each
other by implicit target switching. `--offline` is available only for an
explicitly deferred host-key check; use `test` before any pull.

The response file is created during website enrollment because that workflow
authorizes the submission account and binds the host key. The recovery
tool no longer requires the website for routine pulls, catalog checks or local
bundle verification. The website never receives the private recovery keys.

Do not install a pull timer merely to make application backups automatic; those
uploads already have their own application-host timer. A recovery-client timer
is useful only when a separate workstation must maintain another verified copy.

## Build

The shared Python source runs on Linux and Windows with Python 3.11+,
`paramiko`, and the native `age` tools. Native packaging wrappers are provided
under `tools/linux/recovery-tool/` and `tools/windows/recovery-tool/`; they embed
the platform's `age` and `age-keygen` binaries and emit a SHA-256 sidecar.
