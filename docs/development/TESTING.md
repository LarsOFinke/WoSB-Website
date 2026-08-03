# Teststrategie

Die v1.0-Testbasis hält die Werkzeugkette klein und prüft die produktionsrelevanten Grenzen:

Die Spring-Security-API besitzt ein eigenes Maven-Gate. Es prüft den zum Python-Bestand
kompatiblen PBKDF2- und Session-Tokenvertrag, Host-/Cross-Site-Abweisung und kompiliert alle
MapStruct-Zuordnungen mit Fehlern bei unvollständigen Zielmodellen.

1. **Backend:** Pytest-Module in getrennten Prozessen und Laufzeitverzeichnissen.
2. **Frontend:** Node-eigene Unit-Tests für reine Berechnungen, Crew, Präferenzen und Datum sowie
   gezielte Build-Designer-Regressionen. Ein Architekturtest prüft jede Route-Page auf Page-Model-Bindung und verbietet dort direkte API-/Async-Verantwortung.
3. **Katalog:** Vollständigkeit, Seed-Idempotenz und die Invariante „keine Produktions-Mockdaten“.
4. **Schema-Baseline:** frische Datenbank bis Head, `alembic check`, Downgrade auf `base` und
   erneuter Aufbau aus `0001_baseline`.
5. **Frontend-Build:** Locale-Parität und Vite-Produktionsbuild.
6. **Systemvertrag:** alle Frontend-API-Aufrufe gegen OpenAPI sowie gemeinsame Rollen, Kategorien,
   Statuswerte, MIME-Typen und Upload-Limits.
7. **Infrastruktur:** Bash-Syntax, modulare Runner, Compose-/Env-Vertrag, NGINX-Sicherheitsheader und
   kein Docker-Socket.
8. **Repository:** Versionen, `.cfg`-Konfiguration, Dokumentation, Secrets, öffentliche Registry-URLs, Dateigrößenbudgets, CSS-Layer, gepinnte Container-Basisimages
   und release-freie Runtime-Artefakte.

```bash
make test       # schneller Fachtestlauf
make test-full  # zusätzlich Migration, Build und Infrastruktur
make validate   # vollständiges Release-Gate
make spring-test # gezielter Spring-/MapStruct-Test
```

Neue Funktionen benötigen mindestens Erfolgs-, Berechtigungs- und Fehlerfall. Reine Fachlogik wird
ohne Browser oder Datenbank getestet. End-to-End-Browsertests werden erst eingeführt, wenn ein
kritischer Ablauf nicht zuverlässig über Service-, API- und pure UI-Logik abgedeckt werden kann.

## Testisolation

Der Systemvertrag liegt in `backend/tests/test_frontend_backend_contract.py`. Er liest die
Frontend-API-Module statisch, erzeugt das echte FastAPI-OpenAPI-Schema und vergleicht beide Seiten.
Damit bleibt die fachliche Spiegelung überprüfbar, ohne Frontend und Backend künstlich strukturell
zu koppeln.

`scripts/run_backend_tests.py` startet jedes Backend-Testmodul in einem eigenen Python-Prozess mit
einem eigenen temporären Datenbank-, Upload- und Control-Verzeichnis. Dadurch beeinflussen globale
FastAPI-/SQLAlchemy-Zustände andere Module nicht.
