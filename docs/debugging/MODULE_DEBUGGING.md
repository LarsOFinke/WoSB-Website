# Modulorientiertes Debugging

Dieses Runbook beschreibt den wiederholbaren Weg von einem sichtbaren Fehler bis
zum verantwortlichen Modul. Ziel ist eine kleine, redigierte Evidenzkette und ein
Regressionstest am richtigen Rand. Die Modulverantwortungen stehen im
[Modulkatalog](../architecture/MODULE_CATALOG.md), bereits bekannte
Produktionsursachen im [Incident-Index](DEPLOYMENT_INCIDENTS.md).

## Diagnosevertrag

Eine brauchbare Fehleranalyse beantwortet in dieser Reihenfolge:

1. Welcher öffentliche Ablauf ist betroffen (Methode, Routen-Template,
   Benutzerklasse, erwarteter Status)?
2. Scheitert Transport, Authentifizierung, Autorisierung, Fachlogik, Persistenz,
   Integration oder Darstellung?
3. Welche kleinste reproduzierbare Eingabe zeigt den Fehler ohne Secrets oder
   personenbezogene Daten?
4. Welcher Test verhindert genau diese Ursache künftig?

Nicht in Diagnoseartefakte gehören Request-/Response-Payloads mit Nutzerdaten,
Cookies, CSRF-/Sessiontokens, Webhook-URLs, private Schlüssel, vollständige
IP-Adressen oder unredigierte Datenbankauszüge.

## Lokale Eingrenzung nach Schicht

### API und Backend

1. Route und `operationId` in `openapi/openapi.json` bestimmen.
2. Die Route direkt im Modul-Controller (`@*Mapping`) finden; Request-DTO,
   `@PathVariable`/`@RequestParam` und `@Valid @RequestBody` dort gegen OpenAPI prüfen.
3. Vom Controller zum Service, zur Policy und zum Repository-/Mapper-Rand verfolgen.
4. HTTP-Status einordnen: Transport-/Bean-Binding 400, Authentifizierung 401,
   Autorisierung/CSRF/Origin 403, Zustandskonflikt 409, fachliche Validierung 422.
5. Erst Service-/Policy-Test, bei Security, SQL oder Mapping zusätzlich echten
   HTTP-Test gegen PostgreSQL ergänzen.

```bash
rg -n 'operation_id|operationId|Fehlertext' openapi spring-api/src/main/java
rg -n 'api_error|security_401|security_403' spring-api/src/main/java docs/debugging
mvn -f spring-api/pom.xml -Dtest='<Testklasse>' test
```

Mocktests reichen nicht aus, wenn PostgreSQL-Typen, Constraints, Transaktionen,
Spring Security, CSRF, Cookieattribute oder generierte API-Bindings Teil der
Ursache sind. Dafür liegt der Integrationsrand unter
`spring-api/src/test/java/eu/royalblackwater/api/integration/`.

### Datenbank, Seed und Retention

- Schema ausschließlich über die aktuelle Flyway-Historie erklären; bestehende
  Migrationen nicht zum Debuggen verändern.
- Bei Seedfehlern `seed_key`, gespeicherte Prüfsumme und
  `is_seed_overridden` gemeinsam prüfen. Wiederholung muss idempotent sein.
- JDBC-Werte am Persistence-Rand normalisieren; keine Testfixtures verwenden,
  die PostgreSQL-spezifische Typen unbemerkt ersetzen.
- Retention mit alten, aktuellen, offenen und abgeschlossenen Zeilen testen.
  Eine Löschabfrage darf offene Betroffenenanträge nicht erfassen.
- Vor produktiver Datenkorrektur Upgrade-, Backup- und Recovery-Pfad festlegen;
  Diagnose allein autorisiert keine Mutation.

### Frontend

1. Fehlgeschlagenen Request und HTTP-Status in den Browser-Tools feststellen,
   ohne Header oder Cookies zu kopieren.
2. Route-Page → Page-Composable → API-/Domain-Modul verfolgen.
3. Reine Abbildung/Validierung als Node-Test, Zustandswechsel im Composable und
   kritische Bedienung als Playwright-Smoke absichern.
4. Fehlerzustände müssen sichtbar und wiederholbar bleiben; ein fehlgeschlagenes
   Speichern darf Dialog oder Nutzereingabe nicht voreilig schließen.

```bash
cd frontend
npm run test:unit
npm run test:browser -- --grep '<sichtbarer Ablauf>'
```

Playwright mockt nur `/api/` und beweist UI-Verhalten. Echte Cookie-, Session-,
CSRF-, Rollen- und SQL-Grenzen gehören in Spring-Integrationstests.

### Infrastruktur, Deployment und Recovery

Vom Ursprungssystem sammeln:

```bash
./infrastructure/scripts/diagnostics/debug.sh --area deployment --category errors --since 2h --tail 600
```

Der Collector verwendet die bestehende `.env.origin`-Verbindung, begrenzt die
Remote-Ausgabe und redigiert sie lokal. Bei fehlgeschlagener Aktivierung zuerst
das `failed-*.log`, Servicezustand und Compose-Status sichern. Erst danach darf
eine gezielte, dokumentierte Recovery-Aktion erfolgen. `docker compose down`,
Volume-Löschung oder Änderungen an `shared/data` sind keine ersten
Diagnoseschritte.

## Fehlerklasse → Evidenz → Regressionstest

| Fehlerklasse | Minimale Evidenz | Erwartete Absicherung |
| --- | --- | --- |
| Transport/Contract | Methode, Routen-Template, Status, Bindingdetail | Generator- und Architektur-Check plus Controller-/HTTP-Test |
| Auth/Permission | 401/403, boolesche Cookie-/Origin-/CSRF-Merkmale, Rolle | Security-/Policy-Test und geschützte HTTP-Route |
| SQL/Persistenz | Query-Verantwortung, SQL-State/Constraint, abstrahierte Parameterform | Service-Test plus PostgreSQL-Test |
| Seed/Bootstrap | Seed-Key/Rollen-Code/Status, Wiederholungsablauf | idempotenter Initializer-/PostgreSQL-Test |
| Privacy | Vorgangstyp/Status, keine Inhalte/Identifier | Export-, Pseudonymisierungs- und Retentiontest |
| Frontend-Zustand | Seite, Aktion, HTTP-Status, sichtbarer Zustand | Domain-/Composable-Test und ggf. Browser-Smoke |
| externe Integration | Zielscope, Eventtyp, Delivery-Status, begrenzter Fehler | Policy-/Renderer-Test; Hauptablauf bleibt kontrolliert |
| Deployment | Releaseversion, Phase, Readiness, redigierter Root Cause | Infrastruktur-/Update-/Recovery-Vertragstest |

## Runbook: unerwarteter API-500

Ein generischer `{"detail":"Internal server error."}`-Body ist nur das Symptom.
Für einen 500er wird immer der reale Spring-/PostgreSQL-Pfad reproduziert und der
erste serverseitige Root Cause verfolgt:

1. Den konkreten HTTP-Aufruf in einem Spring-Boot-Integrationstest gegen einen
   PostgreSQL-Testcontainer reproduzieren. Methode, Pfad, Status und einen begrenzten
   Response-Ausschnitt in die Assertion aufnehmen.
2. In Surefire-/Server-Ausgabe die erste `api_error status=500`-Zeile suchen und
   Exceptiontyp sowie den ersten eigenen Stack-Frame notieren. Nicht beim äußeren
   Assertion-Fehler stehen bleiben.
3. Die Route über OpenAPI/operationId → Controller → Service →
   Repository/Mapper verfolgen. Nur den tatsächlich ausgeführten Pfad untersuchen.
4. Bei Spring-JDBC-Fehlern die **fertig zusammengesetzte SQL-Bedeutung** prüfen:
   Fragmentgrenzen, Named-Parameter und Bindings sowie Alias/Spalte gegen Flyway.
   Ein Fehler wie ein zusammengezogener Parametername zeigt häufig fehlenden
   Whitespace zwischen zwei Java-SQL-Fragmenten.
5. `python3 infrastructure/scripts/quality/audit_sql_runtime.py` ausführen und
   benachbarte Query-Kataloge auf dieselbe Fehlerklasse prüfen.
6. Den konkreten Endpoint als dauerhaften Happy-Path-/Regressionstest behalten. Bei
   Filter-/Sortier-SQL zusätzlich den gefilterten Query-Zweig testen.
7. Bei Review-, Admin- oder sonstigen Zustandsautomaten nicht bei einem isolierten
   Request stehen bleiben: echte Voraussetzung erzeugen, Listen-/Detail-Read ausführen,
   Transition durchführen und anschließend den neuen Zustand über HTTP erneut lesen.
   Approve/Reject beziehungsweise Complete/Reject getrennt testen. Eine wiederholte
   bereits verbrauchte Transition muss kontrolliert 4xx liefern und niemals 500.
8. Bei Mapper-/Referenzauflösung optionale Fremdschlüssel ausdrücklich als nullable behandeln.
   Insbesondere niemals `Map.get(RowValues.nullableLong(...))` direkt verwenden: leere
   immutable Maps aus `Map.of()` akzeptieren keinen `null`-Key und können einen normalen
   pending/unreviewed Zustand als `NullPointerException` in einen 500er verwandeln. Erst
   auf `null` prüfen, dann den Lookup ausführen.
9. Danach `ApiSurfaceIntegrationTest` und schließlich `mvn verify` ausführen. Der
   contractweite No-5xx-Sweep, der statische SQL-Audit und die stateful Lifecycle-Tests
   sind drei unabhängige Absicherungen gegen unterschiedliche Laufzeitfehler.

Referenz für Access Review:
`register -> pending -> status=all -> approve -> login -> approved` sowie separat
`register -> pending -> reject -> rejected`. Sentinel-IDs sind für reine Transporttests
zulässig; für stateful Regressionen echte IDs/Datensätze verwenden, damit Repository,
Mapper und Folgeabfragen tatsächlich ausgeführt werden.

Ein 4xx kann im Surface-Sweep fachlich korrekt sein; ein unerwarteter 5xx ist es nie.
Bei einem neuen 500er wird zuerst die Exception behoben, nicht der Test abgeschwächt.

Direkte Diagnosebefehle:

```bash
grep -R -n -A100 -B20 'api_error status=500' spring-api/target/surefire-reports/
python3 infrastructure/scripts/quality/audit_sql_runtime.py
mvn -f spring-api/pom.xml -Dtest=ApiSurfaceIntegrationTest test
```

## Abschluss einer Debugging-Änderung

- Root Cause statt Symptom behoben.
- Erfolgs-, Fehler- und Berechtigungspfad getestet.
- Kein zusätzlicher sensibler Loginhalt eingeführt.
- Betroffene Modulzeile und dauerhaft relevantes Runbook aktualisiert.
- Wiederkehrende, stabile Erkenntnis knapp in
  [`.agents/DEBUGGING_CACHE.md`](../../.agents/DEBUGGING_CACHE.md) gespiegelt.
- `bash .agents/scripts/check-changes.sh --run` und bei querschnittlicher Änderung
  `make validate` erfolgreich.
