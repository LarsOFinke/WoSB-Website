# Sicherheitsrichtlinie

## Unterstützte Version

Nur die aktuelle v1.x-Linie erhält Sicherheitskorrekturen.

## Meldung

Sicherheitsprobleme bitte nicht öffentlich als Issue veröffentlichen. Nutze GitHub Private
Vulnerability Reporting oder kontaktiere den Repository-Betreiber direkt. Beschreibe betroffene
Version, Reproduktionsschritte, Auswirkung und einen möglichen Fix.

## Produktionsgrundsätze

- `.env`, Zugangsdaten, Datenbanken, Uploads und Backups werden nie eingecheckt.
- PostgreSQL ist nur an Loopback gebunden; die API ist ausschließlich über NGINX erreichbar.
- API und Migrationscontainer laufen als unprivilegierter Benutzer und ohne Docker-Socket.
- Admin-Updates akzeptieren nur zwei fest definierte Operationen; Browserdaten werden nicht als
  Shell-Argumente ausgeführt.
- GitHub Actions besitzen standardmäßig nur Leserechte. Produktion nutzt ein geschütztes
  `production`-Environment und einen dedizierten SSH-Schlüssel.
- Vor Migration oder Seed erstellt der Updater ein vollständiges Sicherheitsbackup.

Secrets nach einem Verdacht sofort rotieren: PostgreSQL, Seed-Admin, SSH-Deploy-Key und gegebenenfalls
TLS-Zugangsdaten.

## Secret-Rotation

`setup.sh --regenerate-secrets` ist nur für eine noch nicht initialisierte Installation vorgesehen.
Bei einer bestehenden PostgreSQL-Instanz werden Datenbankrolle, `.env` und abhängige Dienste in
einem geplanten Wartungsfenster gemeinsam rotiert; ein bloßes Überschreiben der `.env` ist verboten.
