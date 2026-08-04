# Royal Blackwater Fleet v1.0.0

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

## Release bauen

CI beziehungsweise eine vollständige Build-Umgebung erzeugt ein source-freies,
prüfsummenbewehrtes Release-Artefakt:

```bash
bash ./deploy.sh
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

Ohne Flags fragt das Skript Ausgabeverzeichnis und Quellrevision interaktiv ab.

Das Zielsystem benötigt weder Git noch Maven, npm oder Zugriff auf Paketregistries.
Es prüft das Bundle und baut nur die minimalen Runtime-Container aus dem bereits
kompilierten Spring-Boot-JAR und dem Vue-`dist`:

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.0.0.tar.gz \
  --checksum rbf-deployment-1.0.0.tar.gz.sha256 \
  --install-root /opt/rbf \
  --env /secure/rbf.env
```

Alternativ genügt `sudo ./setup_website.sh`; dann werden Artefakt, Prüfsumme,
Installationsroot, Environment-Datei und die Erstinstallationsbestätigung im
Terminal abgefragt.

Updates werden durch ein neues Release-Artefakt ausgelöst:

```bash
sudo ./update.sh --artifact /path/to/rbf-deployment-1.0.1.tar.gz
```

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
- [Entwicklung](docs/development/DEVELOPMENT.md)
- [Datenbank und Flyway](docs/development/DATABASE.md)
- [Tests](docs/development/TESTING.md)
- [Deployment](docs/deployment/DEPLOYMENT.md)
- [Installation](docs/deployment/INSTALLATION.md)
- [Betrieb](docs/deployment/OPERATIONS.md)
- [Disaster Recovery](docs/deployment/DISASTER_RECOVERY.md)
- [Sicherheit](SECURITY.md)
- [Änderungsverlauf](CHANGELOG.md)

## Lizenz und Hinweise

Siehe [NOTICE.md](NOTICE.md).
