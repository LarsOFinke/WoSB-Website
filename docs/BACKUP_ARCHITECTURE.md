# Backup- und Recovery-Architektur

Dieses Dokument ist der verbindliche Qualitätsstandard für Änderungen am Backup-Modul, am
Admin-Frontend und am plattformübergreifenden Recovery Tool. Sicherheits- und Betriebsdetails
stehen ergänzend in [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) und
[BACKUP_SERVER_ENROLLMENT.md](BACKUP_SERVER_ENROLLMENT.md).

## Verantwortungsgrenzen

Der Ablauf besitzt drei klar getrennte Grenzen:

1. Das Admin-Frontend erfasst Eingaben, zeigt Status an und sendet typisierte Operationen an die
   API. Es verarbeitet weder SSH-Schlüssel noch Backup-Dateien selbst.
2. Die API validiert Berechtigungen und Requests. Privilegierte Datei-, SFTP- und
   Restore-Operationen werden ausschließlich über den rootseitigen Runner ausgeführt.
3. Das Recovery Tool lädt verschlüsselte Artefakte, prüft deren Integrität und betreibt optional
   ein isoliertes lokales Recovery-Labor. Private age- und Recovery-SSH-Schlüssel verlassen das
   Backup-Gerät nicht.

## Modulstruktur

### Admin-Frontend

| Datei | Verantwortung |
|---|---|
| `useDatabaseBackupsPage.js` | Orchestriert Status, Katalog, Backup-, Restore- und Verbindungsaktionen |
| `useBackupEnrollment.js` | Enrollment-Formular, Antwortdatei und Anwendung der Serverantwort |
| `backupPresentation.js` | Reine Formatierung und Statusdarstellung ohne Netzwerkzugriff |
| `DatabaseBackupsPage.vue` | Deklarative Darstellung und Ereignisbindung |

Neue Enrollment-Funktionen gehören nicht in den Seiten-Orchestrator. Reine Darstellung bleibt
frei von API- und Dateizugriffen.

### Privilegierter Host-Runner

| Datei | Verantwortung |
|---|---|
| `backup-admin-runner.py` | Kleiner Einstiegspunkt, Dispatch und einheitlicher Lebenszyklus |
| `backup_runner_core.py` | Gemeinsamer Status, Logging, Dateizugriff und Validierungsgrundlagen |
| `backup_runner_enrollment.py` | Schlüsselvorbereitung und Enrollment-Protokoll |
| `backup_runner_transfer.py` | SFTP-Konfiguration, Verbindungstest, Transfer und Katalog |
| `backup_runner_restore.py` | Geschützter lokaler PostgreSQL-Restore |
| `backup_metadata.py` | Restore-Metadaten und Kompatibilitätsdeskriptoren |
| `backup_set_manifest.py` | Signierter logischer Backup-Satz und Commit-Marker |

Der Einstiegspunkt enthält keine Protokollimplementierung. Neue Operationen erhalten ein
fachlich benanntes Modul oder werden einer bestehenden, eindeutig passenden Verantwortung
zugeordnet. Secrets dürfen weder Statusdateien noch Logs erreichen.

### Backend-DI

| Komponente | Lebenszyklus und Abhängigkeiten |
|---|---|
| `BackupControlService` | Pro API-Worker einmal erzeugter Orchestrator; erhält Store und UTC-Clock per Constructor Injection |
| `BackupControlStore` | Kleines Protocol für Statuslesen, Requestlesen, Existenzprüfung und atomare Veröffentlichung |
| `BackupControlRepository` | Produktiver Dateisystemadapter mit vorberechneten Pfaden und atomischem Hard-Link-Publish |
| `get_backup_control_service` | Gecachter FastAPI-Provider und zentraler Composition Root |

Routes injizieren den Service über FastAPI und kennen weder Dateipfade noch JSON- oder
Synchronisationsdetails. Der Provider hält keine Datenbankverbindung, offenen Dateien oder
Netzwerksockets; die langlebige Instanz spart lediglich wiederholte Konstruktion und
Pfadauflösung. Tests injizieren einen Memory-Store und eine feste Clock, ohne das Dateisystem zu
verwenden.

DI wird nicht pauschal eingesetzt: Manifestbewertung, Hashing, Zeitstempel-Parsing und andere
reine Transformationen bleiben Funktionen. Kurzlebige Prozesse sowie SFTP-Verbindungen werden
weiter pro Operation geöffnet und zuverlässig geschlossen; deren künstliche Wiederverwendung
würde Fehlerzustände und Ressourcenlecks begünstigen.

### Recovery Tool

| Datei | Verantwortung |
|---|---|
| `app.py` | Aufbau der Tk-Oberfläche und Anwendungslebenszyklus |
| `app_events.py` | Benutzeraktionen, asynchrone Jobs und Ergebnisbehandlung |
| `app_lab.py` | UI-Steuerung des lokalen Recovery-Labors |
| `cli.py` | CLI-Parsing und Dispatch |
| `config.py` | Lokales, secretfreies Profil |
| `sftp_client.py` | Gepinnter SFTP-Transport und atomare Downloads |
| `verification.py` | Entschlüsselung, sichere Extraktion und Manifestprüfung |
| `docker_lab.py` | Isoliertes PostgreSQL-Labor und vollständiger Recovery-Preflight |
| `server_setup.py` | Einmalige, administrative Server-Provisionierung |
| `automation.py` | Lokale Pull-Automatisierung |

GUI, CLI und Server-Provisionierung dürfen keine zweite Implementierung von Transport,
Verifikation oder Laborlogik enthalten; sie rufen die jeweiligen Fachmodule auf.

## Qualitätsregeln

- Eine Klasse oder Funktion bleibt grundsätzlich unter 420 Zeilen; Zielgröße sind 300 bis 400
  Zeilen. Überschreitungen werden durch fachliche Services, Helper oder Orchestratoren getrennt.
- Dateinamen beschreiben eine Verantwortung. Sammeldateien wie `helpers.py`, `utils.py` oder
  `misc.py` sind für neue Fachlogik nicht zulässig.
- Operationen werden an den Systemgrenzen validiert; interne Funktionen erhalten bereits
  normalisierte Werte. Ports liegen beispielsweise immer zwischen 1 und 65535.
- Seiteneffekte bleiben an Adaptern: Dateisystem, Prozesse, Netzwerk und UI. Formatierung,
  Kompatibilitätsbewertung und Manifestlogik bleiben deterministisch testbar.
- Bestehende öffentliche CLI-Befehle, Runner-Operationen und JSON-Verträge werden bei internen
  Aufteilungen stabil gehalten. Vertragsänderungen benötigen Migration, Tests und Dokumentation.
- Temporäre Dateien werden restriktiv angelegt und erst nach erfolgreicher Prüfung atomar
  veröffentlicht. Klartext-Recovery-Daten werden nicht dauerhaft zwischengespeichert.
- Fehlertexte nach außen enthalten keine Secrets oder internen Befehlszeilen. Detaillierte Logs
  bleiben lokal und redigiert.

## Prüf- und Änderungsstandard

Jede Änderung muss mindestens die betroffenen Backend-, Runner-, Recovery-Tool- und
Frontend-Workflow-Tests ausführen. Zusätzlich gelten Ruff, der Repository-Check und der
Frontend-Build als Release-Gates. Sicherheitsrelevante Änderungen benötigen Tests für den
Fehlerpfad, nicht nur für den Erfolgsfall.

Vor einer Erweiterung ist zu prüfen:

1. Gehört das Verhalten bereits zu einem vorhandenen Fachmodul?
2. Kann die Entscheidung als reine Funktion getestet werden?
3. Bleiben geheime Daten und privilegierte Aktionen hinter der bestehenden Systemgrenze?
4. Ist anhand von Datei- und Funktionsname ohne Implementierungslektüre erkennbar, was geändert
   wird?
5. Sind Erfolg, Abbruch, ungültige Eingaben und Wiederholung beziehungsweise Idempotenz getestet?
