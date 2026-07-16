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

### Direct Discord channel webhooks

The API container sends selected application events directly to official Discord channel webhook URLs over the outbound network.
