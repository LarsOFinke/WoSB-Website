# Backup-Server einrichten – Kurzleitfaden

Dieser Ablauf ist der empfohlene Standard. Es werden **keine privaten Schlüssel kopiert**. WoSB und das Recovery-Tool erzeugen und speichern ihre privaten Schlüssel jeweils selbst.

## Voraussetzungen

- WoSB-Webseitenserver und Backup-Server können sich über SSH/SFTP erreichen.
- Auf dem Backup-Server läuft Ubuntu/Debian mit installiertem Recovery Tool.
- Du besitzt Adminrechte in WoSB und `sudo` auf dem Backup-Server.

Recovery Tool auf dem Backup-Server installieren beziehungsweise aktualisieren:

```bash
cd /pfad/zum/deb-verzeichnis
sudo apt install ./rbf-recovery-tool_1.4.2_$(dpkg --print-architecture).deb
rbf-recovery-tool --version
sudo sshd -t
```

Die installierte Version muss mindestens `1.4.2` sein. Das DEB hängt von `pkexec` ab; dadurch kann der spätere Provisionierungsbefehl als normaler Benutzer ausgeführt werden.

## 1. Enrollment-Anfrage in WoSB erstellen

1. Öffne **Staff → Betrieb → Anwendungs-Backups**.
2. Klicke **Anfrage erstellen**.
3. Klicke **Anfrage herunterladen**.
4. Kopiere die heruntergeladene JSON-Datei unverändert in `~/Downloads` auf den Backup-Server.

Die Datei heißt beispielsweise:

```text
rbf-backup-enrollment-<ID>.json
```

## 2. Copy-&-Paste-Befehl erzeugen

Trage in WoSB ein:

- IP oder DNS des Backup-Servers;
- SSH-Port, normalerweise `22`;
- Speicherpfad, empfohlen `/srv/rbf-backups/wosb`;
- Aufbewahrung, beispielsweise `30` Tage;
- optional die IP des WoSB-Servers als `/32`-CIDR.

Klicke **Vollständigen Befehl kopieren** und führe den gesamten Block als normaler Benutzer auf dem Backup-Server aus. Setze kein `sudo` vor den Gesamtbefehl; das Tool fordert die einzelne administrative Freigabe über `pkexec` an.

Der Befehl:

- prüft, ob Anfrage und Recovery Tool vorhanden sind;
- installiert beziehungsweise konfiguriert OpenSSH;
- erzeugt `rbf-backup` und `rbf-recovery`;
- richtet chroot-isoliertes SFTP ein;
- erzeugt age-Identität und Recovery-Leseschlüssel;
- richtet Rotation und lokales Pull-Profil ein;
- schreibt `~/Downloads/rbf-backup-enrollment-response.json`.

Am Ende zeigt das Tool einen `SHA256:...`-Host-Key-Fingerprint und die nächsten Schritte an.

## 3. Antwort importieren

1. Vergleiche den im Terminal ausgegebenen Fingerprint mit dem Fingerprint in WoSB.
2. Wähle in WoSB `rbf-backup-enrollment-response.json` aus.
3. Die Oberfläche muss **Antwort ist gültig** anzeigen.
4. Klicke **Antwort importieren und prüfen**.

WoSB führt danach automatisch aus:

- Live-Host-Key-Vergleich;
- Speicherung der Verbindung im rootgeschützten Hostbereich;
- Aktivierung verschlüsselter Recovery-Bundles;
- SFTP-Upload, atomare Umbenennung, Rückdownload, Bytevergleich und Löschen.

Erst nach diesem vollständigen Test gilt die Verbindung als eingerichtet.

## 4. Erstes Backup testen

Klicke in WoSB **Backup erstellen und übertragen**.

Erwartet im geschützten Host-Log:

```text
Recovery-Preflight bestanden
Koordinierter und vollständig verifizierter Backup-Punkt erstellt
Backup transfer completed
```

Auf dem Backup-Server kann anschließend der read-only Abruf geprüft werden:

```bash
rbf-recovery-tool pull
```

## 5. Schlüssel offline sichern

Auf dem Backup-Server müssen diese beiden Dateien zusätzlich verschlüsselt offline gesichert werden:

```text
~/RBF-Recovery/rbf-recovery-identity.txt
~/RBF-Recovery/rbf-recovery-readonly-ed25519
```

Der private WoSB-Upload-Schlüssel bleibt ausschließlich auf dem Webseitenserver und wird nicht exportiert.

## Häufige Fehler

| Meldung | Ursache und Lösung |
|---|---|
| `Enrollment-Anfrage konnte nicht gelesen werden` | Falscher Dateipfad. Verwende den von WoSB erzeugten vollständigen Dateinamen oder den Copy-&-Paste-Befehl der Oberfläche. |
| `Antwort importieren und prüfen` ist deaktiviert | Zuerst eine aktuelle Anfrage erstellen und eine zur gleichen Enrollment-ID gehörende Antwortdatei auswählen. Die Oberfläche zeigt den konkreten Validierungsfehler an. |
| `String should have at least 32 characters` | Alte manuelle Maske oder falsche Datei. Beim automatischen Enrollment werden weder privater Schlüssel noch Approval-Token benötigt. |
| `Permission denied (publickey)` | Manueller SFTP-Weg mit nicht passendem Schlüssel. Für den Standardweg Enrollment erneut vollständig ausführen. |
| `Received message too long` | SFTP-Konto wurde manuell mit `nologin`, aber ohne `ForceCommand internal-sftp` angelegt. Standard-Provisionierung erneut verwenden. |
| `Connection closed` beim Backup | Das manuelle SFTP-Konto oder der Zielpfad ist nicht schreibbar. Der automatische Enrollment-Test zeigt diesen Fehler bereits vor dem Speichern. |
| `WEBHOOK_ENCRYPTION_KEYS` inkompatibel | Den bestehenden Schlüsselring aus der produktiven Containerumgebung in die geschützte `.env` übernehmen; keinen neuen Schlüssel über bestehende Daten legen. |

## Notfall-Fallback

Die manuelle Verbindungsmaske ist nur für bereits vorhandene SFTP-Infrastruktur gedacht. Sie ist unter **Erweiterte manuelle Einrichtung** eingeklappt. Für eine Neuinstallation immer den Enrollment-Assistenten verwenden.
