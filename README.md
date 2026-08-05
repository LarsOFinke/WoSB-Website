# Royal Blackwater Fleet v1.0.6

Produktionsreifes Fleet-Operations-Portal für **World of Sea Battle** mit Vue 3,
Spring Boot 4, PostgreSQL, Flyway, NGINX und einem artefaktbasierten Deployment.

## Architektur in Kürze

```text
Browser → NGINX → Spring Boot API → PostgreSQL
```

Spring Security bildet die alleinige Sicherheitsgrenze. Das Backend verwendet
validierte Java-Verträge, MapStruct, JDBC/JPA mit expliziten Fetch-Plänen,
Flyway-Migrationen und eingebettete, idempotente Stammdaten. Das frühere
Python-Backend ist nicht mehr Bestandteil der Laufzeit.

## Lokale Entwicklung

Voraussetzungen: Java 21, Maven 3.9+, Node.js 22, npm und PostgreSQL beziehungsweise
Docker für die Integrationstests.

```bash
cp infrastructure/.env.example infrastructure/.env
mvn -f spring-api/pom.xml spring-boot:run
```

In einem zweiten Terminal:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

## Qualitätsprüfung

```bash
make test          # schnelle deterministische Prüfungen
make test-full     # vollständiger Java-/Frontend-/Infrastruktur-Gate
make validate      # identisch zum vollständigen Release-Gate
make check-tree    # sauberer Repository-Baum
```

Ein Release gilt nur dann als auslieferbar, wenn Maven-Kompilierung, Spring- und
PostgreSQL-Integrationstests, Frontend-Tests und Produktionsbuild sowie die
Infrastruktur- und Recovery-Vertragstests erfolgreich waren.

## Release bauen und deployen

CI beziehungsweise eine vollständige Build-Umgebung erzeugt ein source-freies,
prüfsummenbewehrtes Release-Artefakt:

```bash
bash ./infrastructure/scripts/release/build-artifact.sh
```

Für den interaktiven Ursprung-zu-Zielserver-Ablauf genügt anschließend:

```bash
./deploy.sh
```

Der Ursprung überträgt das geprüfte Artefakt und `setup_website.sh` per SSH.
Auf dem Webseitenserver verifiziert `setup_website.sh` das Paket und startet
die atomare Installation. Alle Dialoge können über Flags automatisiert werden.
Die beim ersten Lauf erzeugte `.env.origin` speichert die nicht geheimen
Verbindungs- und Pfadwerte geschützt für spätere Updates; Vorlage:
`.env.origin.example`.

Eine vollständig neue Zielmaschine wird mit `./deploy.sh --configure`
eingerichtet. Der Assistent kann den dedizierten SSH-Administrator und seinen
Deploy-Key über einen einmaligen VPS-Bootstrap-Zugang anlegen und danach im selben
Lauf deployen. Spätere Aufrufe von `./deploy.sh` verwenden diese geprüfte
Konfiguration ohne private Anwendungsaccounts.

Dieselbe Origin-Verbindung dient der begrenzten Produktionsdiagnose:

```bash
./debug.sh
./debug.sh --area calendar --category http-500 --since 30m
```

Die Ausgabe wird auf dem Ursprung redigiert und lokal unter `.diagnostics/`
gespeichert; auf dem Zielsystem entstehen keine dauerhaften Debug-Dateien.

Das Zielsystem benötigt weder Git noch Maven, npm oder Zugriff auf Paketregistries.
Es prüft das Bundle und baut nur die minimalen Runtime-Container aus dem bereits
kompilierten Spring-Boot-JAR und dem Vue-`dist`:

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.0.6.tar.gz \
  --checksum rbf-deployment-1.0.6.tar.gz.sha256 \
  --install-root /srv/rbf \
  --env /secure/rbf.env
```

Alternativ genügt `sudo ./setup_website.sh`; dann werden Artefakt, Prüfsumme,
Installationsroot, Environment-Datei und die Erstinstallationsbestätigung im
Terminal abgefragt.

Updates werden durch ein neues Release-Artefakt ausgelöst:

```bash
sudo ./update.sh --artifact /path/to/rbf-deployment-1.0.6.tar.gz
```

`/tmp/rbf-release` dient nur als kurzlebiges Transfer-Staging. Die persistente
Release-, Konfigurations- und Datenstruktur liegt unter `/srv/rbf`. Eine
bestehende Installation unter `/opt/rbf` wird beim ersten Deployment automatisch
und fail-closed nach `/srv/rbf` migriert.

Rollback, Backup und Restore wechseln Anwendung, Flyway-Schema und persistente
Dateien kontrolliert gemeinsam. Das zum Backup gehörende Release-Artefakt wird im
verschlüsselten Recovery-Bundle mitgeführt.

## Projektstruktur

```text
spring-api/      Spring Boot, Security, Flyway, MapStruct und Fachdomänen
frontend/        Vue 3, modulare UI, Lokalisierung und deterministische Tests
contracts/       versionierter HTTP-, Build-Stat- und Webhook-Vertrag
infrastructure/  Compose, NGINX, Release, Update, Backup und Restore
scripts/         Repository-, Security-, Build- und Packaging-Werkzeuge
tests/           sprachneutrale Recovery- und Infrastruktur-Vertragstests
docs/            Architektur-, Entwicklungs- und Betriebsdokumentation
.github/         CI, Release-Erstellung und Deployment-Promotion
```

## Dokumentation

- [Architektur](docs/architecture/ARCHITECTURE.md)
- [Qualitätsstandards](docs/development/QUALITY_STANDARDS.md)
- [Versionierung](docs/development/VERSIONING.md)
- [Entwicklung](docs/development/DEVELOPMENT.md)
- [Datenbank und Flyway](docs/development/DATABASE.md)
- [API-Nutzung und Sicherheit](docs/reference/API.md)
- [Tests](docs/development/TESTING.md)
- [Deployment](docs/deployment/DEPLOYMENT.md)
- [Installation](docs/deployment/INSTALLATION.md)
- [Betrieb](docs/deployment/OPERATIONS.md)
- [Disaster Recovery](docs/deployment/DISASTER_RECOVERY.md)
- [Sicherheit](SECURITY.md)
- [Änderungsverlauf](CHANGELOG.md)
- [Agent Onboarding](.agents/ONBOARDING.md)

## Lizenz und Hinweise

Siehe [NOTICE.md](NOTICE.md).
