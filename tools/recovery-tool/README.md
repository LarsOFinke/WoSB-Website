# RBF Recovery Tool

Gemeinsamer Python-/Tk-Client für die gefrorenen Windows- und Linux-Recovery-Programme. Er lädt
das neueste verschlüsselte Recovery-Bundle über SFTP mit explizit gepinntem SSH-Host-Key, prüft
die Transport-Prüfsumme, entschlüsselt mit einer ausschließlich lokal vorhandenen age-Identität
und validiert das vollständige Manifest.

Das Profil speichert keine Passwörter oder privaten Schlüssel, sondern nur Pfade und Metadaten.
Downloads erfolgen über `.part`-Dateien mit atomarer Umbenennung. Archive werden auf Pfad-
Traversal, Links, Spezialdateien, Duplikate, Größenlimits und jede Manifest-Prüfsumme geprüft.

## Betriebsarten

```text
rbf-recovery-tool                 grafische Oberfläche
rbf-recovery-tool pull            neuestes Bundle laden und vollständig prüfen
rbf-recovery-tool catalog         Backup-Katalog des Backup-Servers anzeigen
rbf-recovery-tool catalog --json  maschinenlesbaren Backup-Katalog ausgeben
rbf-recovery-tool verify ...      lokales Bundle prüfen
rbf-recovery-tool timer ...       Linux-systemd-Benutzertimer verwalten
rbf-recovery-tool lab ...         lokales PostgreSQL-Recovery-Labor verwalten
rbf-recovery-tool server provision ...  Ubuntu-Backup-Server sicher provisionieren
```

Windows und Linux werden nativ auf dem jeweiligen Betriebssystem gebaut. `age`, `age-keygen`,
Paramiko und ihre nativen Abhängigkeiten werden von PyInstaller eingebettet.

Die verbindlichen Modulgrenzen, Größenbudgets und Testregeln sind in
[`docs/architecture/BACKUP_ARCHITECTURE.md`](../../docs/architecture/BACKUP_ARCHITECTURE.md) festgehalten.

## Linux-spezifisch

Der Linux-Client kann einen systemd-Benutzertimer einrichten und optional ein lokales
PostgreSQL-Recovery-Labor verwenden. Das Labor bevorzugt rootless Docker, bindet PostgreSQL nur
an Loopback und kann den verifizierten DB-Dump aus einem Recovery-Bundle direkt importieren.
Die Docker-Paketinstallation ist bewusst ein getrenntes administratives Hilfsskript; die GUI und
der normale Backup-Client benötigen keine Root-Rechte und verändern keine Firewall.

## Assistierte Backup-Server-Einrichtung

Die Staff-Webseite erzeugt eine öffentliche Enrollment-Anfrage und hält den zugehörigen privaten
SSH-Schlüssel ausschließlich im rootgeschützten Produktivhost-Verzeichnis. Auf einem Ubuntu- oder
Debian-Backup-Server kann das bevorzugt als DEB installierte Tool anschließend einmalig ausführen:

```bash
rbf-recovery-tool server provision \
  rbf-backup-enrollment-REQUEST.json \
  --host backup.example.net \
  --output rbf-backup-enrollment-RESPONSE.json \
  --directory /srv/rbf-backups/wosb \
  --retention-days 30
```

`pkexec` fordert die administrative Freigabe an. Die Benutzer `rbf-backup` und `rbf-recovery` müssen nicht vorab angelegt werden; vorhandene, nicht vom Tool registrierte Konten werden zum Schutz bestehender Zugänge abgelehnt. Das Tool installiert bei Bedarf OpenSSH, richtet
einen dedizierten kennwortlosen Benutzer mit chroot-isoliertem `internal-sftp`, ein rootgeschütztes
`authorized_keys`, den Speicherpfad und einen täglichen Retention-Timer ein. Die private age-
Identität wird im Benutzerkonto des Backup-Geräts erzeugt; nur der öffentliche Empfänger gelangt
in die Antwortdatei. Optional begrenzt `--allow-from <IP/CIDR>` eine bereits aktive UFW-Regel auf
die Produktivserver-Adresse.

Nach dem Import der Antwortdatei prüft der Produktivhost den aktuell ausgelieferten SSH-Host-Key,
pinnt ihn, aktiviert verschlüsselte Recovery-Bundles, testet SFTP und überträgt auch zeitgesteuerte
Backup-Sets automatisch. Private SSH- oder age-Schlüssel werden nicht zwischen den Systemen
ausgetauscht.


### Automatisch getrennter Recovery-Lesezugang

Das Server-Provisioning erzeugt neben dem schreibenden Produktiv-Uploadkonto einen zweiten, nur lokal erreichbaren und durch `internal-sftp -R` read-only erzwungenen Recovery-Zugang. Der zugehörige private SSH-Schlüssel und die private age-Identität verbleiben auf dem Backup-/Recovery-Gerät. Das Tool testet diesen Zugang und speichert automatisch ein lokales Pull-Profil; anschließend genügt `rbf-recovery-tool pull`.

### Backup-Katalog

Die GUI zeigt unter **Backups auf dem Backup-Server** alle vorhandenen
Backup-Set-Manifeste mit UTC-Zeitpunkt, Anlass, Gesamtgröße, Bestandteilen und
Recovery-Status. **Erfolgreich** wird nur angezeigt, wenn das Set committed ist,
alle referenzierten Artefakte und Sidecars vorhanden sind und ihre Größe sowie
Prüfsummenbindung zum Manifest passen. Recovery-Sets benötigen zusätzlich einen
erfolgreichen vollständigen Recovery-Preflight. Unvollständige oder beschädigte
Sets bleiben als **Ungültig** mit Fehlergrund sichtbar.

Der Katalog wird ausschließlich über den gepinnten read-only SFTP-Zugang
gelesen. Auf einem provisionierten Backup-Server verwendet das automatisch
angelegte lokale Profil diesen Zugang, sodass weder Root-Rechte noch Zugriff auf
das Uploadkonto erforderlich sind.
