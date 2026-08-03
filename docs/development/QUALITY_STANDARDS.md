# Verbindliche Qualitätsstandards

Stand: 2. August 2026

Dieses Dokument ist der zentrale Qualitätsvertrag des Projekts. Bei Widersprüchen
gelten Sicherheits- und Datenschutzanforderungen zuerst, danach dieses Dokument
und anschließend die fachspezifischen Architekturdokumente. Abweichungen müssen im
Code oder im zugehörigen Audit mit Grund, Risiko und geplantem Abbau festgehalten
werden.

## 1. Qualitätsziele

- **Korrektheit:** Fachliche Invarianten werden serverseitig erzwungen und getestet.
- **Einfachheit:** Die kleinste verständliche Lösung wird einer vorsorglichen
  Abstraktion vorgezogen (KISS).
- **Klare Verantwortung:** Module haben einen Zweck und stabile Grenzen; SOLID wird
  als Entscheidungsgrundsatz, nicht als Selbstzweck angewandt.
- **Wartbarkeit:** Namen erklären Inhalt, Abhängigkeiten sind sichtbar und Änderungen
  bleiben lokal begrenzt.
- **Betriebsfähigkeit:** Migration, Update, Backup, Restore, Wartung und Diagnose
  besitzen getestete, fehlertolerante Abläufe.
- **Schutz:** Least Privilege, Datenminimierung und sichere Voreinstellungen gelten
  über Anwendung, Infrastruktur, Logs und Integrationen hinweg.
- **Effizienz:** Kritische Backend-Pfade vermeiden unnötige I/O-, Datenbank- und
  Objektarbeit; Optimierungen werden gemessen statt vermutet.

## 2. Architektur- und Dateiregeln

Die verbindlichen Modulgrenzen beschreibt [ARCHITECTURE.md](../architecture/ARCHITECTURE.md).

- Eine Datei hat eine klar benennbare Hauptverantwortung. Ihr Name muss diese ohne
  Öffnen der Datei erkennen lassen.
- Seiten und Routen orchestrieren; Fachlogik, Datenzugriff, Transport, Darstellung
  und statische Kataloge bleiben getrennt.
- Zielgröße für ausführbare Klassen und Module sind höchstens 300–400 Zeilen. Ab
  dieser Größe ist eine Aufteilung nach Verantwortung nachweislich zu prüfen.
- Das Repository-Gate setzt grundsätzlich 420 Zeilen für einzelne ausführbare
  Verantwortlichkeiten durch. Bereichsspezifische, strengere Budgets gelten weiter.
  Kohäsive deklarative Kataloge oder generierter Code dürfen begründet abweichen.
- Dependency Injection ist für zustandsbehaftete Services, externe Adapter,
  Lebenszyklen und Test-Doubles vorgesehen. Reine Berechnungen bleiben einfache
  Funktionen; globale veränderliche Servicezustände sind unzulässig.
- Öffentliche Verträge werden typisiert. Fehler werden fachlich eingeordnet und am
  richtigen Rand in HTTP-, CLI- oder UI-Antworten übersetzt.
- Duplikation wird entfernt, wenn dadurch eine stabile fachliche Regel zentral wird.
  Eine Abstraktion nur für ähnliche Syntax ist kein Qualitätsgewinn.

Automatisierte Größen-, Struktur- und Importregeln liegen in
`scripts/check_repository.py`; sie sind Obergrenzen, keine Zielwerte.

## 3. Backend und Datenbank

- Routen validieren und autorisieren, Services implementieren Anwendungsfälle,
  Modelle bilden Persistenz ab. Transaktionsgrenzen bleiben sichtbar.
- Abfragen vermeiden N+1-Zugriffe, unbegrenzte Ergebnismengen und unnötige
  Serialisierung. Neue Hot Paths erhalten einen messbaren Test oder eine begründete
  Komplexitätsbetrachtung.
- Schemaänderungen benötigen Modell und neue Alembic-Migration. Upgrade auf `head`,
  Schema-Check und der relevante Restore-/Downgrade-Pfad werden geprüft.
- Eingaben werden am Systemrand validiert; SQL, Shell und Dateipfade werden nicht
  durch Stringverkettung aus unkontrollierten Werten erzeugt.
- Backup und Recovery folgen [BACKUP_ARCHITECTURE.md](../architecture/BACKUP_ARCHITECTURE.md) und
  müssen fehlschlagende Teilzustände eindeutig, auditierbar und wiederholbar machen.

## 4. Frontend, CSS und UX

[CSS_ARCHITECTURE.md](../reference/CSS_ARCHITECTURE.md) definiert Design-Tokens, Schichten,
Dateizuschnitt, Responsive-Regeln und Budgets.

- Mobile, schmale und breite Ansichten werden bewusst gestaltet; Media Queries
  basieren auf Inhaltsgrenzen statt einzelnen Geräten.
- Interaktive Elemente funktionieren mit Tastatur, sichtbarem Fokus und sinnvoller
  Semantik. Kontrast sowie `prefers-reduced-motion` werden berücksichtigt.
- Komponenten besitzen vollständige Zustände für Laden, leer, Fehler, deaktiviert
  und Erfolg. Fehlertexte nennen eine mögliche nächste Handlung.
- Globale CSS-Regeln bleiben auf Reset, Tokens und echte Primitiven begrenzt.
  Komponenten- und Seitendesign liegen in eindeutig benannten Dateien.
- Neue Farben, Abstände, Radien und Ebenen verwenden semantische Tokens statt lokal
  verstreuter Konstanten.

## 5. Security und Datenschutz

- Authentisierung, Autorisierung und Objektzugriff werden serverseitig getestet.
- Secrets stammen aus der Laufzeitkonfiguration, werden weder committed noch
  geloggt und sind in Diagnoseausgaben redigiert.
- Personenbezogene Daten werden zweckgebunden minimiert. Neue Felder dokumentieren
  Aufbewahrung, Zugriff sowie Export-, Berichtigungs- und Löschverhalten.
- Logs und Webhooks enthalten nur zur Diagnose oder Aktion notwendige Daten. IP-
  Risikosignale erklären Kriterien, vermeiden aber unnötige Rohdatenweitergabe.
- Abhängigkeiten, Container, Header, Dateirechte und Host-Härtung sind Bestandteil
  der Release-Prüfung. Details und offene Risiken stehen in
  [SECURITY_PRIVACY_AUDIT.md](../audits/SECURITY_PRIVACY_AUDIT.md); für Runtime, Images und
  Container-Isolation gilt zusätzlich [CONTAINER_SECURITY.md](../architecture/CONTAINER_SECURITY.md).

## 6. Tests und Qualitäts-Gates

Jede Fehlerbehebung erhält möglichst einen Regressionstest. Neue Anwendungsfälle
decken Erfolg, erwartete Ablehnung und relevante Fehlerpfade ab. Die Testpyramide
und Befehle beschreibt [TESTING.md](TESTING.md).

Verbindliche Gates sind:

1. Linter und gezielte Unit-/Integrationstests des geänderten Bereichs,
2. Repository-, Security-, CSS- und Infrastruktur-Invarianten,
3. Backend-, Frontend- und Recovery-Tests,
4. Build und Browser-Smoke für lieferrelevante Änderungen,
5. PostgreSQL-Migrations- und historische Recovery-Matrix in CI.

`make validate` bildet die lokale Gesamtabnahme ab. Ein nicht lokal verfügbarer
externer Check wird im Übergabebericht benannt und bleibt durch CI verpflichtend.

## 7. Dokumentation und Änderungen

- Verhalten, Konfiguration, Migration und Betriebsverfahren werden zusammen mit der
  Implementierung aktualisiert. Keine Dokumentation auf Vorrat für nicht vorhandene
  Funktionen.
- `docs/README.md` ist der Einstieg; ein Thema besitzt genau ein führendes Dokument,
  auf das andere Texte verweisen.
- Entscheidungen nennen Kontext, Konsequenz und Grenzen. Beispiele dürfen keine
  echten Zugangsdaten oder personenbezogenen Daten enthalten.
- Commits sind fachlich geschlossen. Pull Requests nennen Problem, Lösung,
  Migration/Seed-Auswirkung, Sicherheits-/Datenschutzfolgen und Testnachweis.

## 8. Definition of Done

Eine Änderung ist abgeschlossen, wenn Verantwortung und Namen klar sind, öffentliche
Verträge stabil oder migriert sind, Fehler- und Berechtigungspfade berücksichtigt
wurden, relevante Tests und Gates bestehen, keine generierten oder geheimen Dateien
enthalten sind und die betroffene Dokumentation den tatsächlichen Stand beschreibt.
