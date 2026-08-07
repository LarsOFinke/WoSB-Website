# Controller-/DTO-Transportrefactoring

Datum: 2026-08-07

## Anlass

Nach der vollständigen Spring-Migration existierten noch zwei historische
Transportstrukturen parallel zur eigentlichen Modularchitektur:

- der Root-Ordner `contracts/`, der OpenAPI, Referenzdaten, Test-Fixtures und ein
  Backup-Protokoll ohne gemeinsamen fachlichen Owner vermischte;
- generierte Java-`*Api`-Interfaces unter `api/contract/api`, die zwischen
  OpenAPI und den Modul-Controllern eine zweite Runtime-Transportebene bildeten.

Die Anwendung verwendet bereits immutable API-DTOs und modulare Controller,
Services, Mapper und Repositories. Die zusätzliche Interface-Schicht lieferte
keine eigene Fachverantwortung und erschwerte Navigation und Ownership.

## Entscheidung

Die externe HTTP-Spezifikation bleibt erhalten, ist aber **kein Backend-Layer**.
Sie liegt nun als `openapi/openapi.json` außerhalb der Java-Runtime-Struktur und
ist die kanonische Quelle für HTTP-Schema, Operationen und API-DTO-Generation.

Generiert werden ausschließlich API-DTOs unter
`spring-api/src/main/java/eu/royalblackwater/api/dto/`. Die 26 Modul-Controller
besitzen ihre Spring-MVC-Mappings und Bean-Validation-Bindings direkt. Ein
statischer Audit vergleicht alle 177 Controlleroperationen mit OpenAPI und
verhindert Drift.

Die Runtime-Abhängigkeit lautet damit:

```text
HTTP
  -> Filter / Security
  -> Controller (Routing + Binding + @Valid API-DTO)
  -> Service (Fachlogik, Policy, Transaktion)
  -> Repository (Persistenz)

Mapper <-> API-/Modul-DTO / Entity / DB-Row
```

Entities bleiben Persistenztypen. API-DTOs bleiben Transporttypen. Services
konstruieren keine API-Repräsentationen; diese Verantwortung liegt in expliziten
Mappern.

## Entfernte Altstrukturen

- `spring-api/.../api/contract/api/*Api.java`
- `generate_spring_routes.py`
- `ContractConversionService`
- Root-Sammelordner `contracts/`
- unreferenzierte `database-metadata.json`

Die weiterhin benötigten Inhalte wurden ihrem Owner zugeordnet:

- OpenAPI: `openapi/openapi.json`
- Build-/Webhook-Referenzdaten: `spring-api/src/main/reference/`
- Build-Berechnungs-Fixtures: `frontend/tests/fixtures/`
- Backup-Protokoll: `infrastructure/scripts/backup/`

## Mapper-Bereinigung

Der generische `ContractConversionService` wurde entfernt. Build-, Ship-,
Master-Data- und Webhook-Konvertierungen sind wieder explizite, typisierte
Mapper. Dynamische Jackson-Konvertierung ist nur innerhalb eines konkreten
Mappers zulässig, wenn die Quelle selbst bewusst dynamisches Integrations-JSON
ist (z. B. Backup-Control-Status).

## Neue Gates

`audit_controller_contract.py` prüft OpenAPI gegen die tatsächlichen
Controllerbindungen. Zusätzlich verbietet `audit_spring_backend.py` die
Wiedereinführung eines Java-`contract`-Layers oder eines generischen
Contract-Konvertierungsservices.

Für API-Änderungen gilt künftig:

1. `openapi/openapi.json` ändern;
2. API-DTOs generieren;
3. den zuständigen Modul-Controller direkt anpassen;
4. Controller-/OpenAPI-Audit ausführen;
5. Service, Mapper, Repository und Tests nur entsprechend ihrer Verantwortung
   ändern.

Damit ist die OpenAPI-Spezifikation weiterhin ein stabiler externer Vertrag,
ohne als parallele Runtime-Architektur missverstanden zu werden.
