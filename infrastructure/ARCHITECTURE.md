# Infrastruktur-Architektur

## Stabile Einstiegspunkte

Die öffentlichen Befehle liegen im übergeordneten Repository:

- `<repo>/deploy.sh --configure` richtet den Testserver ein; Test ist das Standardziel.
- `<repo>/deploy.sh --production --configure` richtet Production explizit ein.
- `<repo>/deploy.sh` und `<repo>/update.sh` delegieren an den Ursprungstransfer;
  `--production` ist für jeden Production-Lauf erforderlich.
- `scripts/diagnostics/debug.sh` folgt derselben Zielauswahl und schreibt
  redigierte Ausgaben lokal am Ursprung.

Die Ziele innerhalb von `infrastructure/` bleiben absichtlich bestehen. Dadurch können die
internen Runtime- und Recovery-Abläufe versioniert und aus dem Dispatcher aufgerufen werden.
Alle gemeinsamen Skripte liegen unter `infrastructure/scripts/`. `quality/` und
`generation/` sind ursprungs-/CI-seitige Module; Host- und Runtime-Module werden
über eine explizite Allowlist gepackt. Im Root bleiben nur `deploy.sh` und
`update.sh`. Eigentümergebundene Helfer in `.agents/scripts/` und
`frontend/scripts/` bleiben bei ihren Modulen.

### Diagnosegrenze

Der Origin-Collector verwendet Host, Benutzer, Port, Installationsroot und
Identity aus dem ausgewählten `.env.origin.test`- beziehungsweise
`.env.origin.production`-Profil. Ohne Flag ist Test aktiv; Production verlangt
`--production`. Er streamt den geprüften Remote-Collector per SSH an
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

### Quality und Generierung

- `scripts/quality/validate.sh`: vollständiges Repository-Gate.
- `scripts/quality/tests/`: Infrastruktur-, Update- und Diagnoseverträge.
- `scripts/generation/`: API-Referenz, Java-Contracts/-Routen, Build-Katalog,
  Flyway-Baseline und Webhook-Vorlagen.

### Kontrollierte Server-Aktionen

- `scripts/services/update.sh`: root-owned Host-Runner für geprüfte Inbox-Artefakte sowie lokale `restart`-/`rollback`-Recovery; normale Artefakte werden weiterhin am Ursprung gebaut und übertragen.
- `scripts/services/restart-application.sh`: startet ausschließlich API und Gateway neu, wartet auf Readiness und lässt PostgreSQL online.

### Direct Discord channel webhooks

The API container sends selected application events directly to official Discord channel webhook URLs over the outbound network.
