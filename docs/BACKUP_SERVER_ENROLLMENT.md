# Assistierte Backup-Server-Einrichtung

> **Schnellstart:** Für die konkrete Einrichtung mit Copy-&-Paste-Befehlen siehe [BACKUP_SETUP_QUICKSTART.md](BACKUP_SETUP_QUICKSTART.md). Dieser Text beschreibt die Sicherheits- und Architekturdetails.

Dieser Ablauf reduziert die manuelle Einrichtung auf den extern erreichbaren Hostnamen, optional
die Quell-IP für UFW und den sichtbaren Vergleich eines SSH-Host-Key-Fingerprints. Es werden nur
öffentliche Enrollment-Dateien ausgetauscht.

## Vertrauensgrenzen

- Der Produktivhost erzeugt und behält den privaten SSH-Upload-Schlüssel.
- Das Backup-Gerät erzeugt und behält die private age-Identität sowie einen getrennten lokalen Recovery-Leseschlüssel.
- Die Anfrage enthält nur den SSH-Public-Key und eine zufällige Enrollment-ID.
- Die Antwort enthält Host, Port, Benutzer, SFTP-Pfad, öffentlichen Host-Key, Fingerprint und
  öffentlichen age-Empfänger.
- Die Antwort wird an die konkrete Enrollment-ID gebunden.
- Vor der Speicherung scannt der Produktivhost den live angebotenen Host-Key und vergleicht ihn
  mit der Antwort. Der Benutzer vergleicht den Fingerprint zusätzlich sichtbar mit der Ausgabe
  des Recovery-Tools.

## Ablauf

1. Staff → Anwendungs-Backups → **Anfrage erstellen**.
2. Anfrage herunterladen und zum Backup-Server übertragen.
3. Recovery-Tool 1.4.2 als Debian-Paket installieren.
4. Keine Linux-Benutzer vorab anlegen: Das Recovery-Tool erzeugt `rbf-backup` und `rbf-recovery` selbst. Bereits vorhandene, nicht vom Tool registrierte Konten werden aus Sicherheitsgründen nicht übernommen.
5. Provisionierung ausführen:

```bash
rbf-recovery-tool server provision REQUEST.json \
  --host backup.example.net \
  --output RESPONSE.json \
  --directory /srv/rbf-backups/wosb \
  --retention-days 30 \
  --allow-from 203.0.113.10/32
```

6. Das Tool prüft den lokalen read-only Recovery-Zugang und schreibt automatisch sein Pull-Profil.
7. Fingerprint in Terminal und Webseite vergleichen.
8. Antwortdatei in Staff auswählen; die Oberfläche validiert Dateiart, Enrollment-ID und alle Verbindungsfelder sichtbar, bevor der Import freigeschaltet wird.
9. Die Webseite prüft live den Host-Key, speichert die Verbindung rootgeschützt, setzt
   `BACKUP_RECOVERY_ENABLED=true`, trägt `BACKUP_AGE_RECIPIENT` ein und führt einen SFTP-Test aus.
10. Ein manuelles Testbackup starten. Danach überträgt auch der tägliche systemd-Backup-Timer
   automatisch vollständige, recovery-verifizierte Sets. Das Set-Manifest wird stets zuletzt als
   Remote-Commit-Marker veröffentlicht.

## Automatisch eingerichtete Backup-Server-Komponenten

- OpenSSH-Server, falls noch nicht installiert;
- dedizierter gesperrter Upload-Benutzer `rbf-backup`;
- separater, nur über `127.0.0.1`/`::1` nutzbarer Recovery-Benutzer `rbf-recovery`;
- root-eigener Chroot unter `/srv/rbf-backups/wosb`;
- setgid-geschütztes `/data`: Upload-Benutzer schreibend, Recovery-Benutzer serverseitig read-only;
- ausschließlich Public-Key-Authentifizierung und `internal-sftp`;
- kein Shellzugang, keine Weiterleitungen, kein TTY und kein Kennwortlogin;
- rootgeschützte zentrale `authorized_keys`;
- private age-Identität und eigener Recovery-Leseschlüssel im Benutzerkonto des Operators;
- getestetes lokales Recovery-Tool-Profil, sodass anschließend `rbf-recovery-tool pull` genügt;
- täglicher Retention-Timer, standardmäßig 30 Tage;
- optionale UFW-Freigabe ausschließlich für eine angegebene Quelle.

## Bewusst manuell

- DNS/IP des Backup-Servers;
- gegebenenfalls die bestehende globale sshd-Portkonfiguration;
- unabhängiger Fingerprintvergleich;
- Aufbewahrung einer zweiten verschlüsselten Kopie der privaten age-Identität und des Recovery-Leseschlüssels;
- regelmäßige vollständige Recovery-Drills.

## Ergebnis des Einmal-Setups

Nach erfolgreichem Provisioning sind Upload und Recovery getrennt:

```text
Produktivserver --SFTP/write--> rbf-backup@Backup-Server:/data
Recovery-Tool  --SFTP/read-only über Loopback--> rbf-recovery@127.0.0.1:/data
```

Das lokale Recovery-Profil wird automatisch gespeichert. Ein späterer Abruf benötigt daher nur:

```bash
rbf-recovery-tool pull
```

Mit `--no-local-profile` kann diese automatische lokale Profilkonfiguration bewusst deaktiviert werden.


## Manuelle Web-Konfiguration ohne Enrollment

Falls der Backup-Server bereits manuell eingerichtet wurde, bleibt der Ablauf ebenfalls vollständig
über den geschützten Host-Runner prüfbar:

1. In **Staff → Betrieb → Anwendungs-Backups** auf **Upload-Schlüssel erzeugen** klicken.
2. Nur den angezeigten öffentlichen Schlüssel beim Benutzer `rbf-backup` in `authorized_keys`
   hinterlegen und den angezeigten Fingerprint dort mit `ssh-keygen -lf authorized_keys` vergleichen.
3. IP/DNS, Port, Benutzer und den innerhalb von SFTP sichtbaren Zielpfad eintragen. Bei einem vom
   Recovery-Tool verwalteten Chroot ist das `/data`; ohne Chroot kann es beispielsweise
   `/srv/rbf-backups/wosb` sein.
4. Den Host-Key ermitteln und den Fingerprint über einen zweiten Kanal prüfen.
5. **Speichern und Schreibtest** ausführen. Die Konfiguration wird erst übernommen, wenn der Runner
   eine zufällige Datei hochladen, atomar umbenennen, wieder herunterladen, bytegenau vergleichen
   und anschließend löschen konnte.

Der separate Button **Schreibtest ausführen** wiederholt genau diesen vollständigen Test. Ein reines
`cd`/`pwd` gilt nicht als erfolgreiche Backup-Verbindung. Die Prüfung und die spätere
Artefaktverifikation verwenden ausschließlich den gepinnten SFTP-Kanal; ein Shellzugang oder
`sha256sum` auf dem Backup-Server ist nicht erforderlich.

## Häufige Abgrenzungen

- `REQUEST.json` ist die von der Webseite heruntergeladene öffentliche Anfrage.
- `RESPONSE.json` ist ausschließlich die Ausgabe von `rbf-recovery-tool server provision`.
- Der private Upload-Schlüssel wird beim Erstellen der Anfrage auf dem Produktivhost erzeugt und niemals exportiert. Beim automatischen Enrollment gibt es daher kein Feld, in das er kopiert werden muss.
- Der in der Oberfläche sichtbare `SHA256:...`-Wert ist der Host-Key-Fingerprint; er ist weder der öffentliche Upload-Schlüssel noch ein privater Schlüssel.
- `--directory` bezeichnet den root-eigenen Speicher-/Chroot-Pfad auf dem Backup-Server. In der Enrollment-Antwort und innerhalb von SFTP bleibt der sichtbare Pfad immer `/data`.
