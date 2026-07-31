# RBF Recovery Tool for Linux

This wrapper creates a native frozen Linux build from the shared source in
`tools/recovery-tool`.

## Target-laptop requirements

After the build, copy only:

- `RBF-Recovery-Tool-Linux-<architecture>`
- the private age identity file, or generate it in the GUI

The target laptop needs no Python, OpenSSH client, age, Docker or PostgreSQL and no inbound
firewall change. It needs a normal graphical Linux session and outbound access to the
server's existing SSH port. Build on the same CPU architecture and on a Linux distribution
with an equal or older glibc baseline than the intended target.

## Build on Debian/Ubuntu

```bash
sudo apt install -y python3 python3-venv python3-tk age build-essential
./Build-RbfRecoveryTool.sh
```

Output example:

```text
dist/RBF-Recovery-Tool-Linux-x86_64
```

On ARM64 the name ends in `aarch64`. Record the printed SHA-256 value and distribute the
binary and checksum through a trusted channel.

## Running

```bash
chmod 700 RBF-Recovery-Tool-Linux-$(uname -m)
./RBF-Recovery-Tool-Linux-$(uname -m)
```

The GUI pins the SSH host key, downloads with SFTP, verifies the sidecar checksum,
decrypts only in a temporary directory and validates every manifest file hash.

## Optional installation in the desktop menu

No root privileges are required:

```bash
./Install-RbfRecoveryTool.sh
```

The script copies the built binary to `~/.local/bin/rbf-recovery-tool` with mode `0700` and
creates `~/.local/share/applications/rbf-recovery-tool.desktop`. It opens no port, installs no
service and changes no firewall rule.
