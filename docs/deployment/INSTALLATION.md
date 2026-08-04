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
`/opt/rbf/shared/.env` mit neuen Secrets und legt die einmaligen Zugangsdaten in
`/opt/rbf/shared/first-run-credentials.txt` ab.

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.0.0.tar.gz \
  --checksum rbf-deployment-1.0.0.tar.gz.sha256 \
  --install-root /opt/rbf \
  --env /secure/rbf.env \
  --no-backup
```

Für einen manuellen Lauf ohne Flags kann `sudo ./setup_website.sh` verwendet
werden. Der Dialog fragt alle Werte ab und verlangt bei einer Erstinstallation
eine ausdrückliche Bestätigung für den fehlenden Backup-Punkt.

`--no-backup` is allowed only for a genuinely new installation without an
existing database. The current origin deployment explicitly combines it with
`--skip-backup` after replacing the active release; this is temporary while the
shared-backup manifest path is being repaired. Do not infer from this that a
database backup exists for every deployment.

For a source-based local setup, `sudo ./setup.sh --profile full` remains available, but it is not the production release path.

## Existing database adoption

Stop the old application, take independent database and file backups, then run the fingerprint and adoption scripts through the provided deployment helpers. The gate accepts only the reviewed final legacy schema; unknown or partial schemas fail closed.
