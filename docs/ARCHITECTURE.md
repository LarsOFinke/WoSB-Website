# Architektur

## Laufzeit

```text
Browser → NGINX Gateway → Spring Boot API Facade → FastAPI → SQLAlchemy → PostgreSQL
                                      └──────────── native auth ────────┘
                                   ↘ Upload-Verzeichnis
Uptime Kuma → internes Gateway/Health-Endpunkte
```

NGINX liefert das Vue-Frontend und leitet alle `/api/**`-Aufrufe an Spring Boot. Die
sicherheitskritischen Sitzungsendpunkte sowie die öffentliche Legal-Notice-Abfrage werden dort
nativ bearbeitet; Registrierung und übrige Fachendpunkte werden während der Übergangsphase intern
an FastAPI weitergereicht. Beide Dienste
verwenden denselben, von Alembic verwalteten PostgreSQL-Vertrag und dasselbe gehashte
Session-Tokenformat.
PostgreSQL bleibt im internen
Compose-Netz; der Loopback-Port dient nur der Host-Wartung. Upload-Inhalte werden nicht direkt aus dem Dateisystem ausgeliefert: `/api/files/{id}/content` und der kompatible `/uploads/...`-Pfad laufen durch die API und antworten ohne öffentlichen Cache. Die ausdrücklich öffentlichen Kontexte `guide`, `forum` und `master-data` bleiben anonym lesbar; sonstige Uploads verlangen den Eigentümer oder Staff-Rechte.

## Backend

### Security-Grenze (Spring Boot)

`spring-api` ist der führende HTTP-Einstiegspunkt und Dienst für Zugangsdatenprüfung, Passwort-Rehashing,
Session-Erzeugung/-Widerruf und den eigenen Benutzerkontext. Java 21, Spring Boot, Spring Security,
JPA und MapStruct werden über Maven gebaut. MapStruct erzwingt vollständige DTO-Zuordnung beim
Kompilieren. Hibernate validiert das vorhandene Schema ausschließlich (`ddl-auto=validate`);
Schemaänderungen bleiben bis zu einer ausdrücklich geplanten Ablösung alleinige Aufgabe von
Alembic.

Der Dienst ist fail-closed: API-Routen werden entweder nativ durch Spring oder während der
schrittweisen Migration über eine interne, nicht öffentlich erreichbare FastAPI-Fassade bedient;
der Actuator-Healthcheck bleibt ausschließlich intern erreichbar. Host- und
Origin/Sec-Fetch-Prüfung ergänzen die NGINX-Limits. Der Container besitzt keinen veröffentlichten
Port, kein allgemeines Outbound-Netz, keine Linux-Capabilities und ein schreibgeschütztes
Root-Dateisystem.

Diese Grenze ist bewusst ein erster Strangler-Schritt, keine Behauptung einer abgeschlossenen
Gesamtmigration. Neue native Spring-Controller ersetzen die Proxy-Zuordnung pro Fachmodul; bis
dahin bleibt FastAPI der interne Besitzer der Fachlogik. Der Browser spricht dabei nur mit Spring.

Fachmodule unter `backend/src/app/modules/<domain>` besitzen nach Bedarf `models`, `schemas`,
`routes` und `services`. Routes übersetzen HTTP, Services enthalten Anwendungslogik, Models bilden
Persistenz ab. Querschnittsthemen liegen in `core` und `db`.

Der Admin-Bereich trennt Systembetrieb, Registrierungen, Security, Inhaltsmoderation und
Benutzerverwaltung in eigene Route-Module. Der Build-Designer hält CRUD und vollständige
Payload-Validierung getrennt; Webhook-Konfiguration und externer Transport sind unabhängige
Services. Die Seed-Orchestrierung ist klein; System-, Schiff- und Build-Option-Katalog werden in getrennten
Modulen synchronisiert. Produktions-Seeds enthalten keine Nutzerinhalte.

Das Privacy-Modul kapselt Consent, Datenexport, Berichtigungs-/Löschanträge und datensparsame
Kontakte. Öffentliche und nutzereigene Routen delegieren an fachliche Services; die Admin-Routen
bilden ausschließlich Prüfung und Freigabe ab. Die irreversible Löschung bleibt damit ein
menschlich freigegebener, technisch deterministischer Vorgang.

## Frontend

`frontend/src/modules/<domain>` kapselt API, Domainlogik, Composables, Seiten und Komponenten. `core` enthält Shell und
Navigation, `shared` wiederverwendbare Technik. Jede Route-Page bindet ausschließlich ein Page-Model; API-Aufrufe, Lifecycle-Ladevorgänge und asynchrone Workflows liegen in Composables. Build-Berechnung, Crew-Zuordnung,
Inventar-Reconciliation, Formular-Defaults, Präferenztransfer und Datumskonvertierung sind reine,
separat testbare JavaScript-Module. Das globale CSS wird über ein geordnetes Manifest aus größenbegrenzten Layern geladen.

## Frontend-Backend-Vertrag

Frontend und Backend spiegeln dieselben Fachmodule und Begriffe, aber nicht dieselbe technische
Schichtenstruktur. Vue-Seiten und Composables konsumieren HTTP-Verträge; FastAPI-Routen und
Application-Services validieren und persistieren die Use-Cases. Ein repositoryweiter Contract-Test
vergleicht alle Frontend-API-Aufrufe mit dem generierten OpenAPI-Schema und schützt gemeinsame
Kategorien, Rollen, Statuswerte, MIME-Typen sowie Upload-Limits vor Drift.

## KISS/SOLID-Leitplanken

- eine fachliche Wahrheit pro Regel; Frontend zeigt, Backend validiert
- keine Abstraktion ohne realen zweiten Anwendungsfall
- UI/Route hängt von Service/Composable ab, nie umgekehrt
- Katalogdaten, Berechnung, Persistenz und Rendering bleiben getrennt
- Soft-Delete für historisch referenzierte Stammdaten
- große Dateien werden nach Verantwortung geteilt; Datenkataloge und Übersetzungen zählen nicht als
  Anwendungslogik
- ausführbare Klassen, Funktionen, Vue-Controller und Stylesheets bleiben nach Möglichkeit im
  Bereich von 300–400 Zeilen; 420 Zeilen sind die technische Obergrenze mit Übergangspuffer
- Repository-Checks begrenzen Python-Klassen/-Funktionen, Vue-Scriptblöcke und sämtliche
  Stylesheets; längere deklarative Datenmodule werden anhand ihrer fachlichen Kohäsion bewertet

## Runtime-Grenzen

Das Backend-Image enthält mit `backend/config/container.env` lediglich eine leere, assignment-freie
Markerdatei für den verpflichtenden Env-Source-Vertrag. Compose lädt `infrastructure/.env` als
Prozessumgebung; Geheimnisse werden nicht in das Image kopiert und nicht als zusätzliches Volume
benötigt.

Laufzeitdaten gehören ausschließlich nach `infrastructure/data`. `.env`, Zugangsdaten, Uploads,
Backups, Caches, Abhängigkeiten und Build-Ausgaben sind nie Teil eines Release-Archivs.
