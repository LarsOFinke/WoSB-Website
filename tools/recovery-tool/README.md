# RBF Recovery Tool

Shared Python/Tk desktop client used to build the frozen Windows and Linux backup clients.
It downloads the latest encrypted recovery bundle over pinned-host-key SFTP, verifies the
transport checksum, decrypts with a local age identity and validates the complete manifest.

The target laptop does not need Python, OpenSSH, age, Docker or PostgreSQL. `age`,
`age-keygen`, Paramiko and their native Python dependencies are included by PyInstaller.
The program only initiates outbound SSH traffic; it opens no listening port and requires no
inbound firewall rule.

Builds are native: create the Windows executable on Windows and the Linux executable on a
compatible Linux build machine for the intended CPU architecture. Both wrappers use this
same source tree and the same PyInstaller specification.

Security properties:

- explicit SHA-256 SSH host-key pinning; no trust-on-first-use connection
- passwords/passphrases kept in memory only
- profile stores metadata and file paths, not secrets
- `.part` downloads and atomic rename
- sidecar SHA-256 verification before decryption
- strict tar path, type, count and uncompressed-size validation
- manifest inventory and per-file SHA-256 verification
- private age identity is generated locally and never uploaded
