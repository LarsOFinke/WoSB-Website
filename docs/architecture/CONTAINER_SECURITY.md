# Docker- und Container-Sicherheitsstandard

Stand: 2. August 2026

Container sind eine zusätzliche Isolationsschicht, keine Sicherheitsgrenze wie eine
eigene VM. Docker Engine, containerd und runc teilen den Host-Kernel; deshalb werden
Runtime, Kernel, Images und Container-Konfiguration gemeinsam gehärtet.

## Aktuelle Risikolage

Für den produktiven Linux-Server sind insbesondere diese Upstream-Fixes relevant:

- Docker Engine 29.5.1 behob mit CVE-2026-41567, CVE-2026-41568 und
  CVE-2026-42306 mehrere Wege, über `docker cp` Code oder Dateien als Host-root zu
  beeinflussen. Bis zum Update darf `docker cp` nicht mit nicht vertrauenswürdigen
  oder kompromittierten Containern verwendet werden.
- Docker Engine 29.5.0 begrenzte mit CVE-2026-32288 die Speicherausschöpfung durch
  präparierte Image-Archive. Unbekannte Images und `docker load` aus fremden Quellen
  bleiben untersagt.
- Aktuelle runc-Releases enthalten Nachbesserungen für die Container-Escapes
  CVE-2025-31133, CVE-2025-52565 und CVE-2025-52881 sowie CVE-2026-41579.
- containerd veröffentlichte unter anderem eine kritische Lücke beim Image-Unpack
  (GHSA-cm76-qm8v-3j95) und 2026 einen UID-Prüfungsbypass. Maßgeblich sind die
  sicherheitsgepflegten Pakete der eingesetzten Linux-Distribution, nicht allein ein
  Vergleich nackter Upstream-Versionsnummern, weil Distributionen Fixes backporten.
- Docker-Desktop-CVEs betreffen den Produktionsserver nicht: Das Projekt verwendet
  dort Docker Engine auf Linux, nicht Docker Desktop oder Model Runner.

Primärquellen: [Docker-Sicherheitsmeldungen](https://docs.docker.com/security/security-announcements/),
[Docker-Engine-29-Release-Notes](https://docs.docker.com/engine/release-notes/29/),
[runc-Releases](https://github.com/opencontainers/runc/releases) und
[containerd-Advisories](https://github.com/containerd/containerd/security/advisories).

## Verbindliche Schutzschichten

### Host und Runtime

1. Kernel, `docker.io`/Docker CE, containerd und runc über eine unterstützte
   Distribution beziehen und Security-Updates täglich installieren. Nach Runtime-
   oder Kernel-Updates Host bzw. Daemon kontrolliert neu starten; nur die
   Paketversion zu aktualisieren ersetzt den laufenden verwundbaren Prozess nicht.
2. `sudo apt update && sudo apt full-upgrade` und `sudo make -C infrastructure doctor`
   vor Freigabe ausführen. Distributions-Security-Tracker prüfen, wenn eine
   Upstream-CVE trotz scheinbar älterer Versionsnummer als gefixt gilt.
3. Docker-API niemals unverschlüsselt per TCP veröffentlichen. Der Socket wird in
   keinen Container gemountet; Mitglieder der `docker`-Gruppe gelten als root.
4. Default-seccomp und AppArmor (beziehungsweise SELinux) aktiviert lassen. Niemals
   `seccomp=unconfined`, `apparmor=unconfined`, `privileged: true` oder Host-PID-/
   Netzwerk-Namespace als bequemen Workaround einführen.
5. Rootless Docker reduziert das Risiko eines Daemon-/Runtime-Exploits und ist für
   neue Installationen zu evaluieren. Die Umstellung ist wegen Ports, systemd,
   Backup-Dateirechten und cgroup-Limits eine geplante Migration, kein stilles
   Setup-Upgrade. Bis dahin schützt die bestehende Trennung: keine Docker-Gruppe,
   minimaler Host und ausschließlich administrative root-Aufrufe.

### Images und Build

1. Nur die im Repository definierten Dockerfiles und vertrauenswürdige Official
   Images bauen. Keine fremden Dockerfiles, BuildKit-Frontends, `docker load`-
   Archive oder unkontrollierten Compose-Overrides auf dem Produktionshost nutzen.
2. Basisimages sind auf konkrete Versionslinien festgelegt. Renovierung erfolgt als
   geprüfte Änderung mit Build, Trivy-Scan und Smoke-Test; `latest` ist unzulässig.
3. Der Security-Workflow baut die Core-Images bei Push, manuellem Lauf und wöchentlich
   neu. Trivy blockiert bekannte `HIGH`- und `CRITICAL`-Schwachstellen mit verfügbarem
   Fix. OSV bleibt ergänzend für Python- und Node-Lockfiles zuständig.
4. Build-Secrets gehören nicht in `ARG`, Image-Layer oder Build-Kontext. Das
   Frontend erhält nur ausdrücklich öffentliche `VITE_*`-Werte.

### Laufende Container

- API, Migration und Seed laufen non-root, read-only, ohne Linux-Capabilities und
  mit `no-new-privileges`.
- Schreibzugriffe sind auf benannte Datenverzeichnisse und `tmpfs` begrenzt.
- Datenbank und interne Dienste werden nicht öffentlich veröffentlicht; lokale
  Diagnoseports binden an `127.0.0.1`.
- PID-Limits, getrennte Netze, Log-Rotation und Healthchecks begrenzen Fehlverhalten.
- Neue Services müssen diese Eigenschaften übernehmen oder ihre minimale Ausnahme
  mit Bedrohung, benötigter Capability und Rückbau dokumentieren.

## Reaktion auf eine neue Runtime-Lücke

1. Betroffene Komponente und laufende Version erfassen:

   ```bash
   sudo docker version
   sudo docker info
   runc --version
   containerd --version
   dpkg-query -W docker.io docker-ce containerd containerd.io runc 2>/dev/null
   ```

2. Exponierung prüfen: Werden fremde Images gebaut/geladen, `docker cp`, Docker-API,
   privilegierte Container, Socket-Mounts oder untrusted Admin-Zugänge verwendet?
3. Paketquellen und Distributions-Advisory prüfen, Security-Update installieren und
   Daemon/Host neu starten. Danach Container mit den neu gebauten Images neu
   erstellen; ein bloßer Image-Pull aktualisiert laufende Container nicht.
4. Bis zur Behebung den betroffenen Pfad deaktivieren. Bei möglichem Escape Host als
   kompromittiert behandeln: isolieren, Zugangsdaten und Backup-Schlüssel rotieren,
   Logs sichern und aus vertrauenswürdigem Stand neu aufsetzen.
5. `make validate`, Security-Workflow und Restore-/Readiness-Prüfung ausführen und
   Entscheidung sowie Advisory im Security-Audit dokumentieren.

## Freigabecheck

```bash
sudo make -C infrastructure doctor
sudo docker compose --env-file infrastructure/.env \
  -f infrastructure/compose.yml config
sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Ein grüner Image-Scan beweist nicht, dass Runtime und Kernel sicher sind. Umgekehrt
ist eine ältere, aber von Debian/Ubuntu gepatchte Paketversion nicht automatisch
verwundbar; entscheidend ist das jeweilige Distribution-Advisory.
