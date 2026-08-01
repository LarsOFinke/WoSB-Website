# Assistierte Backup-Server-Einrichtung

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
3. Recovery-Tool 1.4.0 als Debian-Paket installieren.
4. Provisionierung ausführen:

```bash
rbf-recovery-tool server provision REQUEST.json \
  --host backup.example.net \
  --output RESPONSE.json \
  --directory /srv/rbf-backups/wosb \
  --retention-days 30 \
  --allow-from 203.0.113.10/32
```

5. Das Tool prüft den lokalen read-only Recovery-Zugang und schreibt automatisch sein Pull-Profil.
6. Fingerprint in Terminal und Webseite vergleichen.
7. Antwortdatei in Staff importieren.
8. Die Webseite prüft live den Host-Key, speichert die Verbindung rootgeschützt, setzt
   `BACKUP_RECOVERY_ENABLED=true`, trägt `BACKUP_AGE_RECIPIENT` ein und führt einen SFTP-Test aus.
9. Ein manuelles Testbackup starten. Danach überträgt auch der tägliche systemd-Backup-Timer
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
