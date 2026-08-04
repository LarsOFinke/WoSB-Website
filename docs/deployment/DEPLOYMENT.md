# Deployment

## Build once

CI runs the complete Java and frontend suites, creates the executable Spring Boot JAR and Vue `dist`, then packages a source-free release:

```bash
bash ./deploy.sh
```

The resulting `rbf-deployment-<version>.tar.gz` contains compiled artifacts, minimal runtime Dockerfiles, Compose configuration and version-matched operations scripts. Every file is listed with size and SHA-256 in `manifest.json` and `SHA256SUMS`.

Vom Ursprungsserver aus kann der Transfer interaktiv mit `./deploy.sh`
gestartet werden. Dabei werden Artefakt, Prüfsumme, der Website-Setup-Wrapper
und der Verifier per SSH zum Webseitenserver übertragen; dort übernimmt der
Wrapper die Zielserver-Installation. Für CI stehen entsprechende
Flags zur Verfügung.
Der Zielserver-Bootstrap installiert fehlende Docker-/Compose-Abhängigkeiten
über den bestehenden Host-Paketpfad; `--skip-host` deaktiviert dies explizit.
Die erste interaktive Ausführung legt dafür `.env.origin` (chmod 600) an.
Spätere `deploy`-/`update`-Aufrufe laden diese Konfiguration automatisch;
Flags überschreiben einzelne Werte.

`deploy.sh` und `update.sh` werden auf dem Ursprungsrechner als normaler Benutzer
und ohne `sudo` ausgeführt. Sobald `.env.origin` existiert, läuft ein Aufruf ohne
Flags vollständig nicht-interaktiv. Der Einrichtungsdialog kann bei einer
geänderten Zielmaschine gezielt mit `./deploy.sh --configure` erneut gestartet
werden. Vor dem Build prüft der Dispatcher den Schlüsselzugang und
`sudo -n`; dadurch scheitert eine unvollständige Zielprovisionierung sofort und
ohne lokale oder entfernte Passwortabfrage.

Der Dialog `./deploy.sh --configure` deckt den vollständigen First Run ab. Er
fragt Zielhost, dauerhaften SSH-Admin, dessen Identity, optionalen
Initialbenutzer samt VPS-Key, Port, Staging-Verzeichnis und Artefakt ab. Fehlt der
dedizierte Deploy-Key, kann der Dialog einen Ed25519-Key mit restriktiven
Dateirechten erzeugen. Dieser Key ist absichtlich ohne Passphrase, damit spätere
automatisierte Updates keinen interaktiven Secret-Dialog benötigen; der
Ursprungsrechner und sein Benutzerkonto müssen entsprechend geschützt sein.
Initialbenutzer und Bootstrap-Identity gelten nur für diesen Einrichtungslauf
und werden nicht in `.env.origin` gespeichert.

Auf einem frisch installierten Zielsystem darf `rbfadmin` zunächst fehlen. Der
Dispatcher fragt dann im interaktiven Lauf einmalig nach dem vorhandenen
Initialbenutzer oder akzeptiert `--bootstrap-user USER`. OpenSSH verwendet dafür
automatisch die Host-Konfiguration, den SSH-Agenten und Standard-Keys; nur wenn
der Server es anbietet, bleibt das Passwort als Fallback möglich. Ein bestimmter
VPS-Key kann mit `--bootstrap-identity-file FILE` erzwungen werden; dann sind
`IdentitiesOnly=yes` und `BatchMode=yes` aktiv und es gibt keine Passwortabfrage.
Ein initialer VPS-Account `root` wird direkt verwendet, andere Initialbenutzer
führen den Provisioner über `sudo` aus. Über diese ausdrücklich freigegebene
Verbindung überträgt der Dispatcher nur Provisioner und Public Key, richtet
`rbfadmin` ein, lädt die geprüfte SSH-Konfiguration neu und verifiziert den
Key-only-Zugang. Anschließend setzt derselbe `deploy.sh`-Lauf mit Build, Transfer
und Installation fort. Der Initialbenutzer wird weder in `.env.origin` gespeichert
noch für spätere Updates verwendet.

Beispiele:

```bash
# VPS mit Key aus ~/.ssh/config oder SSH-Agent
./deploy.sh --bootstrap-user root

# VPS mit explizitem Provider-Key und garantiert ohne Passwort-Fallback
./deploy.sh --bootstrap-user ubuntu \
  --bootstrap-identity-file ~/.ssh/provider-vps
```

Der vollständige First-Run-Dialog legt den getrennten Host-Administrator und
seinen Schlüsselzugang an:

```bash
./deploy.sh --configure
```

Für nicht-interaktive Provider-Zugänge stehen zusätzlich `--bootstrap-user`
und `--bootstrap-identity-file` zur Verfügung. Der interne
`infrastructure/setup.sh`-Runner ist kein öffentlicher Deployment-Einstieg.

Der Account ist vom Anwendungsadministrator getrennt, erhält keinen
Docker-Gruppenzugriff, wird per `publickey` authentifiziert und hat keinen
Passwort-, Agent- oder Port-Forwarding-Zugriff. Der private Schlüssel bleibt
ausschließlich beim Administrator und wird nie vom Setup gelesen oder kopiert.
Vor einer öffentlichen SSH-Freigabe muss der neue Zugang in einer zweiten
Sitzung getestet werden; erst danach dürfen globale Root-/Passwort-SSH-Zugänge
deaktiviert werden.

Der Ursprungs-Dispatcher verwendet für diesen Zugang `RBF_DEPLOY_USER` und
`RBF_DEPLOY_IDENTITY_FILE` aus `.env.origin` (Dateimodus `0600`). Ohne explizite
Werte wird `rbfadmin` und – sofern vorhanden – `$HOME/.ssh/rbfadmin` automatisch
verwendet; bei einem abweichenden Zielbenutzer wird entsprechend
`$HOME/.ssh/<zielbenutzer>` geprüft. Der private Schlüssel bleibt ausschließlich
auf dem Ursprungsrechner. Alle SSH-/SCP-Aufrufe
laufen mit `BatchMode=yes` und `IdentitiesOnly=yes`; bei fehlendem oder falschem
Schlüssel wird daher sofort abgebrochen und nicht nach einem Passwort gefragt.
Vor der Umstellung des Dispatchers den Zugang in einer zweiten Sitzung prüfen:

```bash
ssh -o IdentitiesOnly=yes -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no -i ~/.ssh/rbfadmin rbfadmin@target true
```

## Install atomically

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.0.5.tar.gz \
  --checksum rbf-deployment-1.0.5.tar.gz.sha256 \
  --install-root /srv/rbf \
  --env /secure/rbf.env
```

Der Ursprungs-Dispatcher führt vor der Übertragung automatisch einen Cleanup-Lauf
nur für fehlgeschlagene oder unvollständige Releases aus. Der aktive Release wird
niemals vor dem Backup entfernt; ein erneuter Deploy derselben bereits aktiven
Versionsnummer wird daher sicher abgelehnt. `/srv/rbf/shared` mit Environment,
Daten und Diagnosen bleibt erhalten.

Der Installer:

1. verifies outer checksum, safe archive paths and complete inventory;
2. acquires the release lock;
3. uses the verified incoming backup runner against the active release's
   Compose configuration and shared data to create a coordinated
   PostgreSQL/file/recovery backup set before any release switch; activation
   stops if that backup fails;
4. installs `/srv/rbf/releases/<version>`;
5. builds only the small API and gateway runtime images from the JAR and `dist`;
6. switches `/srv/rbf/current` atomically;
7. installs versioned systemd units and runs readiness/smoke tests;
8. writes an activation diagnostic under
   `/srv/rbf/shared/deployments/failed-<version>-<timestamp>.log` and restores
   the previous release where possible on failure.

No Git checkout, Maven, npm or package-registry access is needed on the target host.

The origin dispatcher does not pass `--skip-backup` or `--no-backup` for normal
updates. The target installer therefore invokes the coordinated backup before
the atomic release switch. Using the incoming runner allows a release to repair
backup orchestration defects in its predecessor without mutating that immutable
active release. On a genuinely empty target, `setup_website.sh`
automatically marks the run as a first installation without a backup; if
release data or an active installation is present, it fails closed and keeps
the backup requirement. `--skip-backup` remains an explicit emergency/operator
override and is not part of the origin update path. Direct target-side artifact
activation is not supported; use `./deploy.sh` for a new transfer and
`./update.sh` for every subsequent release.

Bestehende Hosts aus der früheren `/opt/rbf`-Struktur werden beim ersten
Deployment mit dem Installer automatisch migriert. Dabei wird der Stack
kontrolliert gestoppt, die vollständige Release-/Shared-Struktur nach `/srv/rbf`
verschoben und systemd neu verlinkt. Der Installer bricht ab, wenn beide Roots
gleichzeitig existieren oder `current` kein Release zeigt. Danach werden
Artefakte nur noch unter `/tmp/rbf-release` gestaged.

## Promotion

Build each release once. Promote the same checksummed artifact from CI to staging and production. Do not rebuild per environment. Environment-specific values remain in `/srv/rbf/shared/.env`.

## Rollback

```bash
sudo /srv/rbf/current/infrastructure/scripts/release/rollback-release.sh
```

Rollback restores the previous application release; the coordinated backup
artifacts remain available for the explicit database/file restore path.
