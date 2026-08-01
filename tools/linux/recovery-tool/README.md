# RBF Recovery Tool for Ubuntu/Linux

Der Linux-Client wird aus derselben geprüften Python-Codebasis wie die Windows-Version gebaut,
nutzt unter Linux aber zusätzlich systemd-Benutzertimer, SSH-Agent/Schlüssel und ein optionales
rootless-Docker-Recovery-Labor.

## Einfache Installation

Auf einem Ubuntu-Buildsystem:

```bash
sudo apt install -y python3 python3-venv python3-tk age build-essential
./Build-RbfRecoveryTool.sh
```

Der Build erzeugt das native Binary, ein portables Installer-Paket und ein Ubuntu/Debian-Paket.
Zu Beginn werden `build/` und `dist/` vollständig zurückgesetzt. Dadurch kann ein abgebrochener
Neubau kein älteres DEB oder Installer-Archiv als scheinbar aktuelles Ergebnis zurücklassen.
Ein vorheriges `make clean` ist für einen normalen Build daher nicht erforderlich.
Alle Ausgaben und ihre portablen SHA-256-Dateien liegen ausschließlich unter `dist/`:

```text
dist/RBF-Recovery-Tool-Linux-<arch>
dist/RBF-Recovery-Tool-Linux-<arch>-installer.tar.gz
dist/rbf-recovery-tool_1.3.0_<deb-arch>.deb
```

Vor der Installation können die erzeugten Metadaten geprüft werden:

```bash
DEB=./dist/rbf-recovery-tool_1.3.0_$(dpkg --print-architecture).deb
dpkg-deb -f "$DEB" Package Version Architecture Depends
```

In `Depends` muss `pkexec` stehen; `policykit-1` darf nicht vorkommen.
Bevorzugte Installation auf Ubuntu oder Debian:

```bash
sudo apt update
sudo apt install "$DEB"
```

Das Paket hängt direkt von `pkexec` ab. Die veraltete Übergangsabhängigkeit `policykit-1` wird
absichtlich nicht verwendet, damit der Build auch auf aktuellen Ubuntu-/Debian-Versionen
installierbar bleibt.

Prüfsummen lassen sich nach einem Verzeichniswechsel weiterhin prüfen, weil die Sidecar-Dateien
nur den jeweiligen Dateinamen und keinen absoluten Build-Pfad enthalten:

```bash
cd dist
sha256sum -c rbf-recovery-tool_1.3.0_$(dpkg --print-architecture).deb.sha256
```

Danach startet das Tool über das Anwendungsmenü. Das optionale DB-Labor kann dort über
**Rootless Docker einrichten** oder per CLI aktiviert werden:

```bash
rbf-recovery-tool setup --with-db-lab
```

Portable benutzerlokale Alternative:

```bash
tar -xzf RBF-Recovery-Tool-Linux-$(uname -m)-installer.tar.gz
cd RBF-Recovery-Tool-Linux-$(uname -m)-installer
./Install-RbfRecoveryTool.sh
```

Der Installer legt das Programm unter `~/.local/bin/rbf-recovery-tool` ab und erstellt einen
Desktop-Menüeintrag. Profile, Identitäten, Downloads und Lab-Daten bleiben im Benutzerkonto.

Nicht interaktiv:

```bash
./Install-RbfRecoveryTool.sh \
  --binary ./dist/RBF-Recovery-Tool-Linux-$(uname -m) \
  --non-interactive
```

Optionen:

```text
--with-timer   täglichen systemd-Benutzertimer anfordern
--with-db-lab  optionales lokales PostgreSQL-Recovery-Labor einrichten
```

Der Timer kann erst aktiviert werden, nachdem in der GUI ein SSH-Key, ein bestätigter Host-Key
und die private age-Identität konfiguriert wurden.

## Linux-Linux-Automatisierung

Nach der Profilkonfiguration kann der tägliche Pull in der GUI oder per CLI aktiviert werden:

```bash
rbf-recovery-tool timer install
```

Der Benutzer-Timer lädt das neueste Bundle per gepinntem SFTP, prüft die äußere SHA-256-Datei,
entschlüsselt es temporär und verifiziert das vollständige Manifest. Er benötigt keinen
systemweiten Dienst und keine eingehende Firewallregel.

Manueller headless Lauf:

```bash
rbf-recovery-tool pull
```

## Optionales PostgreSQL-Recovery-Labor

Das Labor dient zum regelmäßigen Restore-Test und zur lokalen Datenbankinspektion. Es ist kein
öffentlich erreichbarer Produktionsserver.

Eigenschaften:

- rootless Docker statt Mitgliedschaft in der root-äquivalenten `docker`-Gruppe;
- PostgreSQL wird nur an `127.0.0.1:55432` gebunden;
- zufälliges Kennwort in einer Datei mit Modus `0600`;
- persistentes Docker-Volume;
- read-only Container-Dateisystem, `no-new-privileges`, tmpfs und rotierende lokale Logs;
- derselbe PostgreSQL-Image-Stand wie die Anwendung;
- vollständige Bundle-Prüfung vor dem Datenbankimport.

Bei Installation des Debian-Pakets liegt das privilegierte Provisionierungs-Hilfsskript
rootgeschützt unter `/usr/lib/rbf-recovery-tool`. Die GUI ruft ausschließlich dieses unveränderbare
Skript über PolicyKit auf. Das Rootless-Setup und das Lab selbst laufen danach ausschließlich im
Benutzerkonto. Ein vorhandener rootful Docker-Daemon wird nicht automatisch entfernt oder verändert.

Manuelle Einrichtung:

```bash
pkexec ~/.local/share/rbf-recovery-tool/Provision-RbfRecoveryLab.sh --user "$USER"
~/.local/share/rbf-recovery-tool/Setup-RbfRecoveryLab.sh \
  ~/.local/bin/rbf-recovery-tool
```

CLI:

```bash
rbf-recovery-tool lab status
rbf-recovery-tool lab start
rbf-recovery-tool lab stop

# Reine technische Importprüfung; niemals ein vollständiger Recovery-Nachweis:
rbf-recovery-tool lab import-check \
  --bundle ~/RBF-Recovery/Backups/rbf-recovery-....tar.gz.age \
  --identity ~/RBF-Recovery/rbf-recovery-identity.txt \
  --report ~/RBF-Recovery/import-check.json

# Vollständiger Import-, Migrations-, Schlüssel- und API-Preflight:
rbf-recovery-tool recovery verify \
  ~/RBF-Recovery/Backups/rbf-recovery-....tar.gz.age \
  --identity ~/RBF-Recovery/rbf-recovery-identity.txt \
  --repository ~/Projekte/WoSB-Website \
  --report ~/RBF-Recovery/recovery-preflight.json
```

Die GUI zeigt dafür getrennte Aktionen **Nur DB-Import prüfen** und
**Recovery vollständig prüfen**. Nur der zweite Bericht darf `recoverable=true` enthalten.

## Repository-Hygiene

`build/`, `dist/` und `.venv-build/` sind lokale Builddaten und werden weder versioniert noch in
Release-Archive aufgenommen. Vor einer manuellen Übergabe des Quellbaums kann vom Repository-Root
`make clean-all && make check-tree` ausgeführt werden.
