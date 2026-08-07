# Spring-API Typ- und Importprüfung vom 7. August 2026

## Anlass

Nach dem Layer-, DTO- und Repository-Cleanup wurden IDE-/Compilerfehler zu
fehlenden Imports und inkompatiblen Konvertierungen gemeldet. Die vorherige
Java-Prüfung war bewusst nur ein Parsercheck und konnte solche Symbol- und
Generikfehler ohne vollständige Maven-Abhängigkeiten nicht erkennen.

## Gefundene und behobene Fehler

- `RegistrationService` verwendete `AccountDtoMapper`, ohne den Mapper zu
  importieren.
- `UserAdministrationService` verwendete `AccountDtoMapper`, ohne den Mapper zu
  importieren.
- `PersonalDataExportService` deklarierte die Exportkategorien als
  `Map<String,Object>`, obwohl `PrivacyDtoMapper` und der generierte
  `PersonalDataExportRead` einen
  `Map<String,List<Map<String,Object>>>` erwarten. Die Servicevariable ist nun
  exakt auf den DTO-Vertrag typisiert.
- `RaidHelperProbeService` rief nach dem Mapper-Refactoring noch die entfernte
  Hilfsmethode `result(...)` auf. Der Erfolgsfall verwendet jetzt wie alle
  anderen Probe-Ergebnisse `RaidHelperDtoMapper.profileTestResult(...)`.
- Der letzte nachweislich ungenutzte Import (`HttpStatus.FORBIDDEN` in
  `CalendarService`) wurde entfernt.

## Verbindliche Zielarchitektur

```text
OpenAPI-Vertrag
  -> generierte API-DTOs + generierte *Api-Interfaces
  -> Modul-Controller
  -> Service
  -> Repository -> PostgreSQL
       |
       +-> Mapper -> API-/Modul-DTO
```

Filter und Spring Security liegen vor dem Controller. Controller besitzen die
HTTP-Bindung und delegieren fachliche Arbeit. Services besitzen Fachlogik,
Autorisierung und Transaktionen. Repositories besitzen Persistenz und SQL.
Mapper sind die einzige Repräsentationsgrenze zwischen API-/Modul-DTOs,
Entities und Repository-Zeilen. Generische `model`-Pakete und Operation-Handler
gehören nicht mehr zur Architektur.

## Neue Regression-Sicherung

`infrastructure/scripts/quality/audit_spring_backend.py` prüft zusätzlich alle
Java-Quellen in `src/main` und `src/test` auf:

- Wildcard-Imports;
- doppelte Imports;
- eindeutig ungenutzte Imports;
- Imports auf nicht vorhandene projektinterne Typen;
- häufige fehlende projektinterne Imports bei statischen Typzugriffen.

Diese Offline-Prüfung ergänzt Maven, ersetzt es aber nicht. Generische
Konvertierungen, Konstruktor-/Record-Signaturen, MapStruct-generierter Code und
Framework-APIs werden autoritativ durch `mvn verify` geprüft.

## Prüfung

Die Produktionsquellen wurden mit Java 21 und lokalen Framework-Signaturstubs
vollständig symbolisch typgeprüft. Ergebnis: 465 Produktionsquellen, keine
Compilerfehler. Die 21 Testquellen wurden gegen denselben symbolisch geprüften
Produktionsstand ebenfalls ohne Typfehler kompiliert. Ein AST-basierter
Importcheck über Produktions- und Testquellen meldete keine ungenutzten Imports.
Die verbliebenen 13 statischen `RowValues.*`-Wildcard-Imports wurden auf exakt
die tatsächlich verwendeten Konvertierungsfunktionen reduziert; ein vollständig
ungenutzter Wildcard-Import in `IpBlockService` entfiel dabei komplett. Das
Spring-Architekturaudit ist grün und verbietet Wildcard-Imports künftig.

Zusätzlich wurden fehlende `serialVersionUID`-Deklarationen in den drei eigenen
serialisierbaren Exception-Typen ergänzt. Der erweiterte `-Xlint`-Lauf meldet im
Projektcode nur noch den bekannten Konstruktorhinweis in `UserEntity`, weil dort
die bidirektionale JPA-Profilbeziehung beim Aufbau des Aggregats auf `this`
verweist; dies ist keine inkompatible Konvertierung und kein Importfehler.

Die reguläre Maven-/MapStruct-/Spring-Kompilierung bleibt in einer Umgebung mit
Maven 3.9+ und auflösbaren Dependencies erforderlich; das bereitgestellte
Ausführungsumfeld enthält weiterhin keine Maven-Toolchain und keinen externen
Dependency-Zugriff.
