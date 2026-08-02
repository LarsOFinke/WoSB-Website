# Security- und Datenschutz-Audit — 2. August 2026

## Bewertung und Grenzen

Geprüft wurden der Installationsweg ab einem frisch aktualisierten Debian-/Ubuntu-Server,
Host-Provisioning, systemd, Docker Compose, Netzwerkgrenzen, TLS, NGINX, Backend-Sicherheit,
Datenspeicherung, Retention, Uploads, Webhooks, Backup und Recovery.

Die Prüfung ist eine technische Code- und Konfigurationsanalyse. Sie ersetzt weder eine
Rechtsberatung noch einen externen Penetrationstest oder die Prüfung des tatsächlich betriebenen
Servers, seiner DNS-Zone und seines Routers.

## Ergebnis

Die technische Basis ist für eine kontrollierte Produktivsetzung geeignet. Das Setup installiert
und konfiguriert den Kernstack, Docker, UFW, systemd, TLS-Automatisierung und tägliche
Security-Updates. Es startet den Stack, migriert und seeded die Datenbank und führt Smoke-Tests
vor und nach der TLS-Einrichtung aus.

Eine öffentliche Produktivfreigabe ist trotzdem erst zulässig, wenn die unten genannten
Administrator-Gates erfüllt sind. Insbesondere sind ein selbstsigniertes Zertifikat, eine
unveröffentlichte Datenschutzerklärung oder ein ungeprüfter Restore keine Produktivfreigabe.

## Im Audit geschlossene Befunde

### Automatische Security-Updates fehlten im reproduzierbaren Setup

`unattended-upgrades` wird nun installiert, täglich aktiviert und über systemd-Timer gestartet.
Automatische Neustarts bleiben deaktiviert, damit ein Kernel- oder Runtime-Update nicht
unkontrolliert den Dienst unterbricht. Ein notwendiger Neustart bleibt ein sichtbarer
Administratorvorgang.

### Unnötige root-äquivalente Docker-Gruppenrechte

Das Setup fügt den aufrufenden Benutzer nicht mehr der Docker-Gruppe hinzu. Diese Gruppe gewährt
praktisch Root-Rechte. Anwendung, Update, Backup und Zertifikatserneuerung laufen über eng
definierte rootseitige systemd-Units; der Webprozess erhält weder Docker-Socket noch Host-Shell.

### Firewall-Defaults waren vom Hostzustand abhängig

UFW setzt nun ausdrücklich `deny incoming` und `allow outgoing`, bevor nur SSH, HTTP, HTTPS und
gegebenenfalls der bewusst aktivierte Monitoring-Port freigegeben werden. PostgreSQL und Uptime
Kuma bleiben auf Loopback gebunden. Docker-publizierte Ports werden zusätzlich im Audit geprüft,
weil Docker-Regeln UFW-Regeln umgehen können.

### Fehlende Container-Prozessgrenzen

Alle Compose-Services besitzen nun ein `pids_limit` und einen Init-Prozess. API, Migration und Seed
laufen bereits als nicht privilegierter Benutzer und verwerfen zusätzlich sämtliche Linux-
Capabilities. Alle Services behalten `no-new-privileges`; API und Gateway bleiben read-only.

### Hostzustand war nicht maschinenlesbar prüfbar

`infrastructure/scripts/checks/host-security.sh` prüft automatische Updates, UFW-Defaultregeln,
Docker-Gruppenmitglieder und SSH-Grundeinstellungen. `doctor.sh` bindet diese Prüfung bei einem
Root-Lauf ein. SSH-Passwort- und Root-Login werden gemeldet, aber nicht automatisch abgeschaltet:
Das wäre vor einem nachgewiesenen Schlüsselzugang ein Lockout-Risiko.

### Backup-Vertraulichkeit

Vollständige Recovery-Bundles werden clientseitig mit `age` verschlüsselt, per SHA-256 und Manifest
gebunden und erst nach erfolgreichem Recovery-Preflight als Backup-Satz veröffentlicht. Der private
age-Schlüssel verbleibt auf dem Recovery-Gerät. Enrollment und Restore-Test bleiben bewusst
administratorgeführt.

## Datenschutzbewertung

Die Anwendung unterstützt Datenminimierung und Speicherbegrenzung technisch:

- NGINX-Access-Logs sind deaktiviert.
- Es existiert keine allgemeine Request-Telemetrie in PostgreSQL.
- Sicherheitsrelevante IP-Signale werden tagesaggregiert und standardmäßig sieben Tage gehalten.
- Audit-, Webhook-, Consent-, Registrierungs- und Sessiondaten besitzen automatisierte Fristen.
- Sessiontokens werden serverseitig nur gehasht gespeichert; Cookies sind HttpOnly, Secure und
  SameSite-geschützt.
- Discord-Webhook-Zugangsdaten werden authentifiziert verschlüsselt und API-seitig maskiert.
- Uploads werden anhand tatsächlicher Dateisignaturen geprüft und privat ausgeliefert.

Die konkreten Fristen stehen in [DATA_RETENTION.md](DATA_RETENTION.md). Ihre rechtliche
Angemessenheit und Rechtsgrundlage muss der Verantwortliche für den tatsächlichen Betrieb prüfen.

## Offene Administrator- und Go-live-Gates

### Blockierend

1. Verantwortlicher, Zwecke, Rechtsgrundlagen, Empfänger, mögliche Drittlandtransfers,
   Aufbewahrungsfristen und Betroffenenrechte müssen in einer rechtlich geprüften
   Datenschutzerklärung veröffentlicht werden.
2. Impressum beziehungsweise Anbieterkennzeichnung muss mit den tatsächlichen Betreiberangaben
   geprüft und veröffentlicht werden.
3. DNS und öffentlich vertrauenswürdiges TLS müssen von einem externen Netz geprüft werden.
   `CERTIFICATE_PROVIDER=self-signed` ist für öffentlichen Betrieb nicht freigegeben.
4. Das Backup-System muss enrollt, ein verschlüsselter Backup-Satz übertragen und ein vollständiger
   Restore auf einem getrennten System protokolliert werden.
5. Bootstrap-Zugangsdaten müssen nach der Erstanmeldung aus dem Server-Dateisystem entfernt und
   sicher verwahrt oder vernichtet werden.

### Vor öffentlicher SSH-Freigabe

1. Einen zweiten administrativen SSH-Zugang mit Schlüssel testen.
2. Danach `PasswordAuthentication no` und `PermitRootLogin no` setzen.
3. Effektive Konfiguration mit `sshd -T` prüfen und eine bestehende Sitzung bis zum erfolgreichen
   Neuverbindungstest offen halten.
4. Vorhandene Mitglieder der Docker-Gruppe entfernen, sofern sie nicht ausdrücklich als
   root-äquivalente Administratoren autorisiert sind.

### Weiter offen

- Uptime Kuma 1.23.16 benötigt die bereits dokumentierte, kontrollierte Major-Migration auf die
  aktuelle Produktlinie. Das optionale Monitoring sollte bis dahin nicht öffentlich exponiert
  werden.
- Gateway- und Runtime-Images benötigen regelmäßig einen Image-/SBOM-Scan zusätzlich zum
  Lockfile-basierten OSV-Scan.
- Der technische Export-, Berichtigungs- und Löschworkflow ist umgesetzt. Der Verantwortliche muss
  weiterhin Identitätsprüfung, gesetzliche Fristen und mögliche Aufbewahrungspflichten organisatorisch
  festlegen und dokumentieren.
- Discord ist ein externer Empfänger. Aktivierte Ereignisse und Templates müssen auf
  Datenminimierung und den konkreten Rechtsrahmen geprüft werden.
- Ein externer Penetrationstest gegen Produktivdomain, API und tatsächlich erreichbare Ports bleibt
  vor einer breiten öffentlichen Freigabe empfohlen.

## Automatisierter Weg vom frischen Server

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot

git clone <REPOSITORY_URL> WoSB-Website
cd WoSB-Website
sudo ./setup.sh \
  --profile core \
  --domain example.org \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@example.org

sudo make -C infrastructure doctor
```

Das Core-Profil vermeidet die zusätzliche öffentliche Monitoring-Oberfläche. Das Setup übernimmt
Pakete, Docker/Compose, Verzeichnisse und Rechte, Firewall, systemd, Secrets, Datenbankmigration,
Seed, Build, Start, Zertifikat und Smoke-Test. Interaktiv bleiben ausschließlich Entscheidungen,
die Identität, Recht, externe Vertrauensanker oder Wiederherstellbarkeit betreffen.

## Verifikation

Reproduzierbare lokale Gates:

```bash
python scripts/security_audit.py
python scripts/check_repository.py
bash scripts/test-infrastructure.sh
sudo infrastructure/scripts/checks/host-security.sh
sudo make -C infrastructure doctor
```

Die Offline-Prüfung kontrolliert unter anderem Secret-Muster, Action-Pins, Containergrenzen,
Firewall- und Update-Setup, Cookie-Schutz, Webhook-Verschlüsselung, Uploadgrenzen, Backup-
Verifikation und Recovery-Isolation.

## Maßgebliche Primärquellen

- [Art. 5 und Art. 32 DSGVO (EUR-Lex)](https://eur-lex.europa.eu/eli/reg/2016/679/art_32/oj/eng)
- [Datenschutzgrundsätze der Europäischen Kommission](https://commission.europa.eu/law/law-topic/data-protection/rules-business-and-organisations/principles-gdpr_en)
- [Ubuntu Server: Automatic updates](https://ubuntu.com/server/docs/how-to/software/automatic-updates/)
- [Docker Engine security](https://docs.docker.com/engine/security/)
- [Docker Linux post-installation](https://docs.docker.com/engine/install/linux-postinstall/)
