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

1. Route und `operationId` in `contracts/api-contract.json` bestimmen.
2. Generierten Controller nur lesen; zuständigen Operation-Handler über die
   `operations()`-Menge finden.
3. Service, Policy und Repository-/Mapper-Rand verfolgen.
4. HTTP-Status einordnen: Transport-/Bean-Binding 400, Authentifizierung 401,
   Autorisierung/CSRF/Origin 403, Zustandskonflikt 409, fachliche Validierung 422.
5. Erst Service-/Policy-Test, bei Security, SQL oder Mapping zusätzlich echten
   HTTP-Test gegen PostgreSQL ergänzen.

```bash
rg -n 'operation_id|operationId|Fehlertext' contracts spring-api/src/main/java
rg -n 'api_error|security_401|security_403' spring-api/src/main/java docs/debugging
mvn -f spring-api/pom.xml -Dtest='<Testklasse>' test
```

Mocktests reichen nicht aus, wenn PostgreSQL-Typen, Constraints, Transaktionen,
Spring Security, CSRF, Cookieattribute oder generierter Transport Teil der
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
| Transport/Contract | Methode, Routen-Template, Status, Bindingdetail | Generator-Check plus Handler-/HTTP-Test |
| Auth/Permission | 401/403, boolesche Cookie-/Origin-/CSRF-Merkmale, Rolle | Security-/Policy-Test und geschützte HTTP-Route |
| SQL/Persistenz | Query-Verantwortung, SQL-State/Constraint, abstrahierte Parameterform | Service-Test plus PostgreSQL-Test |
| Seed/Bootstrap | Seed-Key/Rollen-Code/Status, Wiederholungsablauf | idempotenter Initializer-/PostgreSQL-Test |
| Privacy | Vorgangstyp/Status, keine Inhalte/Identifier | Export-, Pseudonymisierungs- und Retentiontest |
| Frontend-Zustand | Seite, Aktion, HTTP-Status, sichtbarer Zustand | Domain-/Composable-Test und ggf. Browser-Smoke |
| externe Integration | Zielscope, Eventtyp, Delivery-Status, begrenzter Fehler | Policy-/Renderer-Test; Hauptablauf bleibt kontrolliert |
| Deployment | Releaseversion, Phase, Readiness, redigierter Root Cause | Infrastruktur-/Update-/Recovery-Vertragstest |

## Abschluss einer Debugging-Änderung

- Root Cause statt Symptom behoben.
- Erfolgs-, Fehler- und Berechtigungspfad getestet.
- Kein zusätzlicher sensibler Loginhalt eingeführt.
- Betroffene Modulzeile und dauerhaft relevantes Runbook aktualisiert.
- Wiederkehrende, stabile Erkenntnis knapp in
  [`.agents/DEBUGGING_CACHE.md`](../../.agents/DEBUGGING_CACHE.md) gespiegelt.
- `bash .agents/scripts/check-changes.sh --run` und bei querschnittlicher Änderung
  `make validate` erfolgreich.
