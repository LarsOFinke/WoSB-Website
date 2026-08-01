# Disaster Recovery und Desktop-Backup

Dieses Verfahren ist für einen vollständigen Verlust des Raspberry Pi ausgelegt. Ein Recovery-Bundle enthält:

- einen konsistenten PostgreSQL-Dump;
- Uploads, Zertifikate, Let's-Encrypt-Konfiguration und optional Uptime Kuma;
- `infrastructure/.env` einschließlich der Datenbank- und Verschlüsselungsschlüssel;
- die vier versionsverwalteten `backend/config/*.cfg` als überprüfbaren Snapshot;
- optionale First-Run-Zugangsdaten;
- root-seitige Remote-Backup-Secrets und `known_hosts`;
- Betriebssystem-, Paket-, Docker-, Architektur-, Versions- und Commit-Metadaten;
- ein Manifest mit Größe und SHA-256 für jede enthaltene Datei;
- einen nicht geheimen Fingerprint-Snapshot des Verschlüsselungsschlüsselrings, damit ein Restore vor Aktivierung auf Schlüsselkontinuität geprüft werden kann.

Das Gesamtarchiv wird mit **age** für einen öffentlichen Empfänger verschlüsselt. Der private age-Schlüssel bleibt ausschließlich auf dem verschlüsselten Backup-Laptop (BitLocker oder LUKS) und einer zweiten sicheren Offline-Ablage. Ein Angreifer auf dem Pi kann vorhandene Bundles damit weder entschlüsseln noch neue gültige Empfänger ableiten.

## 1. Recovery-Tool für Windows oder Linux vorbereiten

Windows- und Linux-Client verwenden dieselben geprüften Python-Quellen unter
`tools/recovery-tool`. Die nativen Build-Wrapper liegen unter `tools/windows/recovery-tool`
und `tools/linux/recovery-tool`. Auf dem Backup-Laptop benötigt das fertige Programm weder
Python noch OpenSSH, Docker, PostgreSQL oder eine eingehende Firewall-Regel. Paramiko, `age`
und `age-keygen` sind im jeweiligen PyInstaller-Artefakt enthalten.

### Windows-Build

```powershell
cd tools\windows\recovery-tool
Set-ExecutionPolicy -Scope Process Bypass
.\Build-RbfRecoveryTool.ps1
```

Ausgabe:

```text
tools\windows\recovery-tool\dist\RBF-Recovery-Tool-Windows.exe
```

### Linux-Build

Der Linux-Build muss nativ für die gewünschte Architektur erzeugt werden. Auf Debian/Ubuntu:

```bash
sudo apt install -y python3 python3-venv python3-tk age build-essential
cd tools/linux/recovery-tool
./Build-RbfRecoveryTool.sh
```

Ausgabe beispielsweise:

```text
tools/linux/recovery-tool/dist/RBF-Recovery-Tool-Linux-x86_64
tools/linux/recovery-tool/dist/RBF-Recovery-Tool-Linux-aarch64
```

Das Linux-Ziel benötigt nur eine normale grafische Sitzung und die üblichen Desktop-/glibc-
Laufzeitbibliotheken. Es sollte auf derselben CPU-Architektur und mit einer nicht neueren
glibc-Basis gebaut werden als das Zielsystem.

Optional ohne Root-Rechte ins Linux-Anwendungsmenü installieren:

```bash
./Install-RbfRecoveryTool.sh
```

Das Skript installiert ausschließlich das Binary unter `~/.local/bin` und einen Desktop-Eintrag.
Es richtet keinen Dienst ein, öffnet keinen Port und ändert keine Firewallregel.

Beim ersten Start:

1. neben **age-Identität** auf **Neu** klicken;
2. den privaten Schlüssel in einem BitLocker- oder LUKS-geschützten Ordner speichern;
3. den angezeigten öffentlichen `age1...`-Empfänger auf dem Pi konfigurieren;
4. den SSH-Host-Key über einen zweiten Kanal prüfen und in der GUI fest pinnen;
5. Zielordner und Serverprofil speichern.

Die GUI speichert keine Kennwörter oder privaten Schlüssel, sondern nur deren lokale Pfade.
Passwörter beziehungsweise Schlüssel-Passphrasen bleiben nur für den aktuellen Vorgang im
Speicher. Der private age-Schlüssel verbleibt auf dem Backup-Laptop und in einer zweiten verschlüsselten
Offline-Ablage.

Die bisherigen PowerShell-Skripte bleiben als administrativer Fallback verfügbar:

```powershell
winget install FiloSottile.age
winget install Python.Python.3.13
.\tools\windows\New-RbfRecoveryKey.ps1
```

## 2. Pi konfigurieren

Den öffentlichen Wert aus `rbf-recovery-recipient.txt` in `infrastructure/.env` eintragen:

```dotenv
BACKUP_RECOVERY_ENABLED=true
BACKUP_AGE_RECIPIENT=age1...
BACKUP_PULL_EXPORT_DIR=/home/smokenougat/rbf-backups
BACKUP_PULL_EXPORT_USER=smokenougat
```

Danach die Host-Abhängigkeiten und systemd-Units aktualisieren:

```bash
sudo ./setup.sh --profile full --no-start
sudo systemctl start rbf-hub-backup.service
```

Der tägliche Timer erzeugt einen koordinierten Backup-Satz aus Datenbank und Laufzeitdateien.
Wenn die API aktiv ist, wird sie standardmäßig kurz angehalten, damit beide Artefakte dieselbe
Anwendungsgrenze repräsentieren. Anschließend wird der neue Dump in einer isolierten Datenbank
importiert, auf den aktuellen Alembic-Head migriert und mit Schlüssel- sowie API-Readiness-Test
verifiziert. Erst der danach erzeugte Backup-Set-Commit-Marker macht den Lauf zu einem gültigen
Produktions-Recovery-Punkt.

Bei aktivierter Recovery-Funktion entsteht zusätzlich unter
`infrastructure/data/backups/recovery` ein age-verschlüsseltes Bundle. Ein manueller
Staff-Panel-Lauf überträgt Artefakte und Prüfsummen atomar, anschließend den Recovery-Bericht und
zuletzt das Backup-Set-Manifest als Remote-Commit-Marker.

## 3. Vom Windows- oder Linux-Laptop abrufen und vollständig prüfen

Im **RBF Recovery Tool**:

1. **Host-Key prüfen** und den Fingerprint unabhängig vergleichen;
2. **Neuestes Backup laden** auswählen;
3. die standardmäßig aktive vollständige Prüfung eingeschaltet lassen.

Das Tool:

1. verbindet sich ausgehend per SFTP mit dem bestehenden SSH-Port;
2. berücksichtigt nur einen zuletzt veröffentlichten Backup-Set-Commit-Marker mit gültiger Prüfsumme;
3. verlangt darin ein gebundenes Recovery-Bundle und einen erfolgreichen vollständigen Preflight-Bericht mit `recoverable=true`;
4. lädt Set, Bericht, Bundle und sämtliche Sidecars über temporäre `.part`-Dateien und benennt sie erst nach Abschluss um;
5. prüft die Transport-Prüfsummen und die Bindung von Dateiname, Größe und SHA-256 im Backup-Set;
6. entschlüsselt das Bundle ausschließlich temporär auf dem lokalen Laptop;
7. lehnt Pfad-Traversal, Links, Spezialdateien, Duplikate und unerwartete Archivwurzeln ab;
8. verifiziert Größe und SHA-256 jeder Manifestdatei;
9. entfernt anschließend alle temporären Klartextdaten.

Alte Sidecar-only-Exporte ohne Recovery-Bericht und Backup-Set-Commit werden bewusst nicht mehr automatisch ausgewählt.

Die Verbindung akzeptiert keinen stillschweigend neuen SSH-Host-Key. Eine Änderung des
gepinnten Fingerprints blockiert den Download, bis sie unabhängig untersucht wurde.

PowerShell-Fallback im Repository-Checkout:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\windows\Pull-RbfRecovery.ps1 `
  -Server "smokenougat@server" `
  -RemoteDirectory "/home/smokenougat/rbf-backups" `
  -Destination "C:\Users\User\Desktop\DB-Backups\RBF"
```

Der Laptop muss für das serverseitige Backup nicht eingeschaltet sein. Er zieht die bereits
verschlüsselte Exportkopie beim nächsten manuellen Lauf ab. Für unbeaufsichtigte Aufgabenplanung
bleibt das PowerShell-Skript die vorgesehene Schnittstelle; die GUI ist bewusst interaktiv.

## 4. Wiederherstellung auf einem frisch installierten Pi

Voraussetzungen:

- Raspberry Pi OS Lite oder Debian 64-bit;
- Netzwerk und SSH;
- Repository-Checkout, vorzugsweise derselbe Release oder ein neuerer kompatibler Stand;
- Recovery-Bundle, `.sha256` und die private age-Identität temporär auf dem Pi.

Minimale Vorbereitung:

```bash
sudo apt update
sudo apt install -y age git

git clone <REPOSITORY_URL> ~/WoSB-Website
cd ~/WoSB-Website
```

Bundle und Identität beispielsweise vom Backup-Laptop übertragen:

```powershell
scp "C:\Users\User\Desktop\DB-Backups\RBF\rbf-recovery-....tar.gz.age*" smokenougat@server:/tmp/
scp "$HOME\RBF-Recovery\rbf-recovery-identity.txt" smokenougat@server:/tmp/
```

Linux-Alternative:

```bash
scp ~/RBF-Recovery/Backups/rbf-recovery-....tar.gz.age* smokenougat@server:/tmp/
scp ~/RBF-Recovery/rbf-recovery-identity.txt smokenougat@server:/tmp/
```

Dann auf dem Pi:

```bash
cd ~/WoSB-Website
sudo ./infrastructure/scripts/backup/restore-recovery.sh \
  --yes \
  --identity /tmp/rbf-recovery-identity.txt \
  --bundle /tmp/rbf-recovery-YYYYMMDDTHHMMSSZ.tar.gz.age
```

Das Restore-Skript:

1. prüft die äußere SHA-256-Datei;
2. entschlüsselt und verifiziert das vollständige Manifest;
3. stellt `.env`, First-Run-Datei und root-seitige Backup-Secrets wieder her;
4. legt die gesicherten `.cfg` standardmäßig nur unter `infrastructure/data/recovered-config` zur Prüfung ab;
5. provisioniert Docker, Firewall und systemd reproduzierbar;
6. stellt Uploads, TLS/Let's Encrypt und Uptime Kuma wieder her;
7. baut die API und das Gateway;
8. importiert PostgreSQL zunächst in eine isolierte Staging-Datenbank;
9. migriert und prüft dort Schema sowie verschlüsselte Webhook- und Raid-Helper-Zugangsdaten;
10. schaltet die geprüfte Datenbank atomar aktiv und hält die vorherige Datenbank bis zum erfolgreichen Readiness-/HTTPS-Smoke-Test als automatischen Rollback bereit;
11. führt anschließend den idempotenten Seed und die abschließenden Betriebsprüfungen aus.

Nur wenn bewusst ein exakt gleicher alter Code-Checkout verwendet wird, können die gesicherten `.cfg` direkt zurückgespielt werden:

```bash
sudo ./infrastructure/scripts/backup/restore-recovery.sh \
  --yes \
  --restore-versioned-config \
  --identity /tmp/rbf-recovery-identity.txt \
  --bundle /tmp/rbf-recovery-YYYYMMDDTHHMMSSZ.tar.gz.age
```

Auf einem bereits initialisierten Ziel verweigert das Skript den Lauf standardmäßig. Eine bewusste In-Place-Wiederherstellung benötigt zusätzlich `--replace-existing`; für einen Hardwareausfall ist ein frischer Datenträger beziehungsweise eine frische OS-Installation vorzuziehen.

Nach Erfolg den privaten Schlüssel unverzüglich vom Pi entfernen:

```bash
sudo shred -u /tmp/rbf-recovery-identity.txt 2>/dev/null || sudo rm -f /tmp/rbf-recovery-identity.txt
```


## 5. Geschützter PostgreSQL-Restore im Admin-Panel

Das Admin-Panel kann den vorgesehenen lokalen Ordner
`infrastructure/data/backups/postgres` katalogisieren. Der Browser kann weder einen Pfad noch
einen freien Dateinamen übermitteln. Der root-seitige Runner akzeptiert ausschließlich:

- reguläre `.sql`- oder `.sql.gz`-Dateien mit sicherem Namen;
- eine passende `.sha256`-Sidecar-Datei;
- Dateien, die ohne Symlink-Folge geöffnet und während der Prüfung nicht verändert wurden;
- eine undurchsichtige, aus Name, Größe und Prüfsumme abgeleitete Backup-ID.

Ein Restore ist ausschließlich für den Bootstrap-Admin freigeschaltet und benötigt zusätzlich
eine bewusste Host-Freigabe:

```bash
cd ~/WoSB-Website
sudo ./infrastructure/scripts/backup/arm-admin-restore.sh
```

Der Befehl zeigt einen einmaligen, standardmäßig zehn Minuten gültigen Token. Im Admin-Panel:

1. **Lokale Backups prüfen**;
2. den verifizierten Dump auswählen;
3. den einmaligen Host-Token eingeben;
4. exakt `RESTORE DATABASE` bestätigen;
5. die abschließende Browser-Bestätigung akzeptieren.

Neue PostgreSQL-Backups besitzen zusätzlich eine checksummierte `.restore.json`-Sidecar-Datei. Sie enthält ausschließlich nicht geheime Metadaten wie Alembic-Revision und Fingerprints des beim Backup verfügbaren Schlüsselrings. Das Admin-Panel markiert bekannte Schlüsselkonflikte und lässt solche Dumps nicht auswählen. Bei älteren Dumps ohne Metadaten erfolgt dieselbe Prüfung verbindlich in der isolierten Staging-Datenbank.

Der Klartext-Token wird weder in API-Antworten noch in Audit-Logs oder der Host-Warteschlange
gespeichert. Die API persistiert lediglich seinen SHA-256-Wert. Der Host löscht die root-geschützte
Freigabe vor der Auswertung, sodass auch ein falscher Versuch den Token verbraucht. Die kurzlebige
Freigabedatei wird ausdrücklich nicht in Recovery-Bundles aufgenommen. Anschließend
verwendet der Restore-Runner exklusiven Lock und ein zusätzliches Pre-Restore-Backup. Import, Migration und Schlüsselprüfung geschehen zunächst ohne Downtime in einer Staging-Datenbank. Nur für den atomaren Datenbanktausch werden API und Gateway kurz gestoppt. Scheitert danach die Anwendung, wird die vorherige Datenbank automatisch zurückgeschaltet und erneut gestartet.

Ein reiner Datenbank-Dump enthält bewusst keine geheimen Entschlüsselungsschlüssel. Wird ein Dump auf einem neu installierten Host verwendet, muss deshalb entweder das vollständige Recovery-Bundle eingesetzt oder der alte Schlüsselring vor dem Restore aus der gesicherten `infrastructure.env` zusammengeführt werden:

```bash
sudo ./infrastructure/scripts/backup/merge-encryption-keyring.sh \
  /pfad/zur/alten-infrastructure.env
```

Das Werkzeug behält den neuen Primärschlüssel bei, ergänzt alte Schlüssel nur als Entschlüsselungs-Fallback, erzeugt vorher eine `.env`-Sicherung und gibt keine Schlüsselwerte aus. Nach erfolgreichem Start werden Webhooks auf den aktuellen Primärschlüssel rotiert; Raid-Helper-Zugangsdaten sollten anschließend im Staff-Panel neu gespeichert und getestet werden.

Ein kompromittiertes normales Admin-Konto reicht damit weder für die Auswahl eines beliebigen
Dateisystempfads noch zum Start eines Datenbank-Restores aus. Der Ablauf ersetzt dennoch keine
Multi-Faktor-Authentifizierung und keinen sicheren SSH-/Hostbetrieb; er bildet eine zusätzliche
physische beziehungsweise Host-seitige Freigabeschranke.


## Aus dem realen Restore-Test abgeleitete Schutzregeln

- `psql`-Variablen werden ausschließlich über Standardeingabe/Here-Documents verarbeitet; die fehleranfällige Kombination aus `-c` und `:'variable'` ist im Restore-Pfad verboten.
- Ein optionales, nicht entschlüsselbares Integrationstoken darf den API-Start nicht blockieren. Betroffene Webhooks werden deaktiviert und müssen durch einen Administrator neu gespeichert werden.
- Ein Datenbank-Restore wird niemals direkt über die aktive Datenbank geschrieben. Die aktive Datenbank bleibt bis zum erfolgreichen Anwendungs-Smoke-Test als Rollback erhalten.
- Fehlende oder ungültige SHA-256-Sidecars werden bei jedem Restore abgelehnt.
- Ein DB-only-Restore und ein vollständiger Bare-Metal-Restore sind unterschiedliche Vertrauenspfade: Nur das verschlüsselte Recovery-Bundle enthält `.env`, `.cfg`, Zertifikate und Host-Secrets.
- Nach jedem Recovery-Test wird unmittelbar ein neues vollständiges Recovery-Bundle erstellt und extern verifiziert.


## Raspberry-Pi-Produktionsgrundlage

Ein Restore-Verfahren ersetzt keine stabile Hardwarebasis. Für einen produktiven Pi 4 gelten mindestens:

- aktive Kühlung oder ein dauerhaft ausreichend dimensioniertes Lüftergehäuse;
- offizielles beziehungsweise hochwertiges 5,1-V-Netzteil und kurzes geeignetes Kabel;
- SSD statt verschleißanfälliger SD-Karte, sofern möglich;
- freie Luftzufuhr und Temperatur-/Throttling-Alarmierung;
- optional USV/HAT für kontrolliertes Herunterfahren bei Stromausfall;
- ein vorbereitetes Ersatzmedium oder ein zweiter Pi für Restore-Übungen.

Nach Hardware- oder Temperaturauffälligkeiten sind `vcgencmd get_throttled`, Kernel-Logs, Dateisystem und ein vollständiger Recovery-Test zu prüfen. Wiederholte `Illegal instruction`, I/O-Fehler oder unerklärliche Containerabstürze sind ein Grund für Hardware-/OS-Neuaufbau statt Weiterbetrieb auf Verdacht.

## 6. Recovery-Ziele und Übungen

Empfohlene Betriebsziele:

- **RPO:** maximal 24 Stunden bei täglichem Timer; geringer, wenn der Timer häufiger konfiguriert wird.
- **RTO:** 30–60 Minuten für frisches OS, Checkout, Restore und Smoke-Test.
- mindestens zwei Kopien des privaten age-Schlüssels an getrennten, verschlüsselten Orten;
- mindestens eine erfolgreich verifizierte Recovery-Kopie außerhalb des Pi;
- monatliche Windows-Inhaltsprüfung;
- vierteljährlicher Restore-Test auf Ersatzmedium oder separatem Pi, ohne die Produktion zu überschreiben.

Ein Backup gilt erst als belastbar, wenn es außerhalb des Quellsystems liegt, entschlüsselt werden kann, alle Manifest-Prüfsummen stimmen und ein Restore-Test erfolgreich war.

## Linux-Backup-Laptop und lokales Restore-Labor

Auf Ubuntu kann das gefrorene Recovery-Tool als benutzerlokale Anwendung installiert werden.
Der Build erzeugt dafür ein Debian-Paket und zusätzlich ein portables Installer-Archiv:

```bash
cd tools/linux/recovery-tool
./Build-RbfRecoveryTool.sh
sudo apt update
sudo apt install ./dist/rbf-recovery-tool_1.4.0_$(dpkg --print-architecture).deb
```

Das Paket verwendet `pkexec` als direkte PolicyKit-Laufzeitabhängigkeit und ist damit auch auf
aktuellen Ubuntu-/Debian-Versionen installierbar, auf denen das alte Übergangspaket
`policykit-1` nicht mehr angeboten wird. Buildausgaben bleiben unter `dist/`; ihre
SHA-256-Sidecars enthalten portable Dateinamen statt absoluter Buildpfade.

Das Debian-Paket ist der bevorzugte Weg, weil das optionale privilegierte Docker-Hilfsskript
rootgeschützt installiert wird. Die portable Benutzerinstallation bleibt für Systeme ohne
Paketinstallation verfügbar.

Der Installer kann optional einen täglichen systemd-Benutzertimer und ein lokales
PostgreSQL-Recovery-Labor einrichten. Der normale Client benötigt weiterhin weder Docker noch
administrative Rechte.

Das DB-Labor verwendet bevorzugt Docker Rootless Mode. Die administrative Vorstufe installiert
Docker Engine und Compose aus dem offiziellen Ubuntu-Repository sowie die Rootless-
Voraussetzungen; die eigentliche Docker-Instanz und alle Container laufen anschließend im
Benutzer-Namespace. Der Benutzer wird ausdrücklich nicht in die root-äquivalente `docker`-Gruppe
aufgenommen.

PostgreSQL ist ausschließlich unter `127.0.0.1:55432` erreichbar. Es wird kein Port an eine
LAN-/WAN-Adresse gebunden und keine Firewallregel erzeugt. Die Lab-Konfiguration und das zufällige
Kennwort liegen mit Modus `0600` unter dem XDG-Benutzerdatenverzeichnis. Der Container nutzt ein
read-only Root-Dateisystem, `no-new-privileges`, tmpfs für Laufzeitpfade, ein persistentes Volume
und begrenzte lokale Docker-Logs.

Das Recovery-Tool trennt zwei Nachweisstufen sichtbar:

1. **Nur DB-Import prüfen** validiert Verschlüsselung, Sidecar und Bundle-Manifest, importiert den
   Dump mit `ON_ERROR_STOP` und führt eine SQL-Probe aus. Der Bericht setzt immer
   `recoverable=false`, weil weder Migrationen noch die Anwendung geprüft wurden.
2. **Recovery vollständig prüfen** baut das aktuelle Backend aus einem ausgewählten Repository,
   importiert den Dump in das rootless Labor, bewertet den Alembic-Graphen, führt
   `alembic upgrade head` und `alembic check` aus, prüft den Schlüsselring und startet die API in
   einem internen Docker-Netz ohne veröffentlichte Ports. Nur dieser vollständige Lauf darf
   `recoverable=true` melden.

Temporäre Klartextdaten werden anschließend entfernt. Die JSON-Berichte dokumentieren Quelle,
Kompatibilitätsstatus und jeden einzelnen Prüfschritt.
