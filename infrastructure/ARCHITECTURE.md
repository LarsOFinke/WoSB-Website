# Infrastruktur-Architektur

## Stabile Einstiegspunkte

Die öffentlichen Befehle liegen im übergeordneten Repository:

- `<repo>/setup.sh` delegiert an `infrastructure/setup.sh`.
- `<repo>/update.sh` delegiert an `infrastructure/scripts/services/update.sh`.

Die Ziele innerhalb von `infrastructure/` bleiben absichtlich bestehen. Dadurch können die
übergeordneten Wrapper, systemd-Units und Admin-Panel-Aufrufe unverändert weiterarbeiten.

## Verantwortlichkeiten

### Setup

- `setup.sh`: kompatibler, dünner Runner.
- `scripts/setup/options.sh`: CLI, Standardwerte und Eingabevalidierung.
- `scripts/setup/workflow.sh`: Reihenfolge des First-Run-Setups.
- `scripts/setup/main.sh`: Composition Root; verbindet Optionen, Host und Docker.

### Host-Provisionierung

`scripts/lib/host.sh` ist eine kompatible Fassade. Die Implementierung ist getrennt nach:

- `scripts/lib/host/packages.sh`: Betriebssystempakete und Docker.
- `scripts/lib/host/storage.sh`: Runtime-Verzeichnisse, Besitzer und Rechte.
- `scripts/lib/host/firewall.sh`: UFW-Regeln.
- `scripts/lib/host/tls.sh`: Bootstrap- und Let's-Encrypt-Zertifikate.

### Server-Update

- `scripts/services/update.sh`: kompatibler Runner für den Repository-Entry-Point und systemd.
- `scripts/update/options.sh`: CLI und Update-Modus.
- `scripts/update/request.sh`: Admin-Panel-Anforderung.
- `scripts/update/status.sh`: atomare Statuspersistenz.
- `scripts/update/repository.sh`: Git und Migrationserkennung.
- `scripts/update/workflow.sh`: Backup, Build, Deployment und Smoke-Test.

### Discord-Bot

- `scripts/services/manage-discord-bot.sh`: kompatibler systemd-Runner.
- `scripts/discord-bot/context.sh`: Pfade und Host-Konfiguration.
- `scripts/discord-bot/git.sh`: nicht-interaktiver Git-Transport.
- `scripts/discord-bot/service.sh`: systemd- und Installationsstatus.
- `scripts/discord-bot/request.sh`: Admin-Panel-Anforderung.
- `scripts/discord-bot/status.sh`: atomare Statuspersistenz.
- `scripts/discord-bot/configuration.sh`: Aufruf der Konfigurationsvalidierung.
- `scripts/discord-bot/apply-configuration.py`: Validierung und atomisches Schreiben der Bot-Konfiguration.
- `scripts/discord-bot/actions.sh`: Installieren, Aktualisieren, Konfigurieren und Dienststeuerung.

## Erweiterungsregeln

Neue CLI-Optionen gehören in das jeweilige `options.sh`; neue Betriebsaktionen in das fachlich
passende Workflow- oder Actions-Modul. Entry-Points sollen keine Fachlogik enthalten. Gemeinsam
genutzte Funktionen werden nur dann in `scripts/lib/` verschoben, wenn mindestens zwei Bereiche
sie tatsächlich benötigen.
