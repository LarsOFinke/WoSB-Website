# Infrastruktur-Architektur

## Stabile Einstiegspunkte

Die öffentlichen Befehle liegen im übergeordneten Repository:

- `<repo>/deploy.sh --configure` ist der vollständige First-Run-Einstieg.
- `<repo>/deploy.sh` und `<repo>/update.sh` delegieren an den Ursprungstransfer unter `scripts/release/deploy-from-origin.sh`.
- `<repo>/debug.sh` delegiert an `scripts/diagnostics/collect-from-origin.sh`
  und schreibt redigierte Diagnoseausgaben lokal am Ursprung.

Die Ziele innerhalb von `infrastructure/` bleiben absichtlich bestehen. Dadurch können die
internen Runtime- und Recovery-Abläufe versioniert und aus dem Dispatcher aufgerufen werden.
Allgemeine Repository-Prüfungen und Generatoren bleiben im top-level `scripts/`;
Runtime-/Hostskripte gehören wegen ihrer Artefakt- und Zielsystemverantwortung
unter `infrastructure/scripts/`.

### Diagnosegrenze

Der Origin-Collector verwendet Host, Benutzer, Port, Installationsroot und
Identity aus `.env.origin`. Er streamt den geprüften Remote-Collector per SSH an
`sudo -n bash`, ohne ihn oder Rohlogs auf dem Ziel zu speichern. Der Remote-Teil
liest nur systemd- und Compose-Logs beziehungsweise Dienststatus. Erst am
Ursprung werden IP-Adressen, E-Mail-Adressen, Querywerte und Zugangsdaten
redigiert; die begrenzte Ausgabe landet mit restriktiven Rechten unter
`.diagnostics/` oder einem expliziten lokalen Pfad.

## Verantwortlichkeiten

### Internes Host-Setup

- `setup.sh`: interner Runner für lokale Entwicklung und Artefaktinstallation;
  kein öffentlicher Root-Wrapper.
- `scripts/setup/options.sh`: CLI, Standardwerte und Eingabevalidierung.
- `scripts/setup/workflow.sh`: Reihenfolge des First-Run-Setups.
- `scripts/setup/main.sh`: Composition Root; verbindet Optionen, Host und Docker.

### Host-Provisionierung

`scripts/lib/host.sh` ist eine kompatible Fassade. Die Implementierung ist getrennt nach:

- `scripts/lib/host/packages.sh`: Betriebssystempakete und Docker.
- `scripts/lib/host/storage.sh`: Runtime-Verzeichnisse, Besitzer und Rechte.
- `scripts/lib/host/firewall.sh`: UFW-Regeln.
- `scripts/lib/host/tls.sh`: Bootstrap- und Let's-Encrypt-Zertifikate.

### Kontrollierte Server-Aktionen

- `scripts/services/update.sh`: root-owned Host-Runner für geprüfte Inbox-Artefakte sowie lokale `restart`-/`rollback`-Recovery; normale Artefakte werden weiterhin am Ursprung gebaut und übertragen.
- `scripts/update/options.sh`: CLI sowie Update- und Neustartmodus.
- `scripts/update/request.sh`: Admin-Panel-Anforderung.
- `scripts/update/status.sh`: atomare Statuspersistenz.
- `scripts/update/repository.sh`: Git und Migrationserkennung.
- `scripts/update/workflow.sh`: kontrollierter Anwendungsneustart oder Backup, Build, Deployment und Smoke-Test.
- `scripts/services/restart-application.sh`: startet ausschließlich API und Gateway neu, wartet auf Readiness und lässt PostgreSQL online.

### Direct Discord channel webhooks

The API container sends selected application events directly to official Discord channel webhook URLs over the outbound network.
