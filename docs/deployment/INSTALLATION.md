# Installation

Production requires a 64-bit Debian/Ubuntu-class host, Docker Engine with Compose v2, at least 2 GiB RAM, adequate backup storage, DNS and TCP 80/443.

## Prepare shared configuration

Create a private environment file from `infrastructure/.env.example`, replace every generated/example secret and configure hostname, database, session, encryption and backup settings. Store it root-readable only.

## First artifact install

Der empfohlene Ursprungspfad ist `./deploy.sh`. Auf dem Zielserver kann
`setup_website.sh` alternativ direkt interaktiv oder mit Flags ausgeführt werden.
Fehlen Docker oder Compose, verwendet der Assistent automatisch den vorhandenen
Host-Bootstrap aus `infrastructure/scripts/lib/host/packages.sh`. Mit
`--skip-host` kann dieser Schritt bewusst deaktiviert werden.
Wird keine Environment-Datei angegeben, erzeugt der Assistent automatisch
`/srv/rbf/shared/.env` mit neuen Secrets und legt die einmaligen Zugangsdaten in
`/srv/rbf/shared/first-run-credentials.txt` ab.

Bei einer wirklich leeren Zielinstallation erkennt `setup_website.sh` den
Erstinstallationsfall automatisch und setzt intern die notwendige Bestätigung.
Sobald aktive oder nicht eindeutig verwaiste Release-Daten vorhanden sind,
bleibt der Backup-Schutz aktiv und der Lauf bricht ohne manuelle Entscheidung
ab.

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.0.7.tar.gz \
  --checksum rbf-deployment-1.0.7.tar.gz.sha256 \
  --install-root /srv/rbf \
  --env /secure/rbf.env \
  --no-backup
```

Für einen manuellen Lauf ohne Flags kann `sudo ./setup_website.sh` verwendet
werden. Der Dialog fragt alle Werte ab und verlangt bei einer Erstinstallation
eine ausdrückliche Bestätigung für den fehlenden Backup-Punkt.

`--no-backup` remains restricted to a genuinely new installation without an
existing database. Normal updates always create the coordinated backup before
the release switch.

Der öffentliche First-Run-Einstieg ist `./deploy.sh --configure`. Das interne
Quellbaum-Setup unter `infrastructure/setup.sh` wird nur noch von lokalen
Entwicklungs- und Artefaktabläufen verwendet und ist kein stabiler
Produktionsvertrag.

## Existing database adoption

Stop the old application, take independent database and file backups, then run the fingerprint and adoption scripts through the provided deployment helpers. The gate accepts only the reviewed final legacy schema; unknown or partial schemas fail closed.
