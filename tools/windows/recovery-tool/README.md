# RBF Recovery Tool for Windows

This wrapper creates the native Windows executable from the shared source in
`tools/recovery-tool`.

## Target-laptop requirements

After the executable has been built, the target laptop needs only:

- `RBF-Recovery-Tool-Windows.exe`
- the private age identity file, or generate it in the GUI
- outbound network access to the server's existing SSH port

No Python, OpenSSH client, age, Docker, PostgreSQL, inbound firewall rule or Windows service
is required. SFTP is embedded through Paramiko and `age.exe`/`age-keygen.exe` are bundled.

## Build once on Windows

Install Python 3.13 and the official Windows `age.exe`/`age-keygen.exe` pair on a trusted
build computer. Then run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Build-RbfRecoveryTool.ps1
```

Or provide both age binaries explicitly:

```powershell
.\Build-RbfRecoveryTool.ps1 `
  -AgeExecutable "C:\Tools\age\age.exe" `
  -AgeKeygenExecutable "C:\Tools\age\age-keygen.exe"
```

Output:

```text
dist\RBF-Recovery-Tool-Windows.exe
```

Record the printed SHA-256 value and distribute the EXE through a trusted channel. PyInstaller
must create the Windows executable on Windows; the Linux wrapper builds separately from the
same Python source.

## First use

1. Enter host, SSH port, username and remote recovery directory.
2. Select a local destination and age identity, or use **Neu** to generate one locally.
3. Optionally select a dedicated SSH private key.
4. Select **Host-Key prüfen** and independently compare the displayed fingerprint.
5. Save the profile and select **Neuestes Backup laden**.

Deep verification checks transport SHA-256, age decryption, archive structure, manifest
inventory and every contained file hash. Passwords and private-key passphrases are not saved.
