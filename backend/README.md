# RBF Backend

FastAPI-Anwendung mit SQLAlchemy 2, Alembic und fachlich getrennten Modulen.

## Lokale Entwicklung

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.lock
pip install --no-deps -e .
cp .env.example .env
rbf-dev
```

Nicht geheime Einstellungen liegen nach Verantwortlichkeit getrennt in `config/*.cfg`.
Laufzeitwerte und Geheimnisse werden aus der verpflichtenden `.env` gelesen; echte
Prozessvariablen überschreiben gleichnamige `.env`-Werte. Ein alternatives Verzeichnis
kann über `RBF_CONFIG_DIR` gesetzt werden, eine einzelne `.cfg`-Datei weiterhin über
`RBF_CONFIG_FILE`.

Die vollständige Testbasis wird vom Repository-Root über `make test` ausgeführt; Produktion
nutzt ausschließlich PostgreSQL, Alembic und explizite System-/Stammdaten-Seeds.
Python-Caches lassen sich mit `./scripts/clear-pycache.sh` entfernen.

Siehe `ARCHITECTURE.md`, `CONFIGURATION.md` und `REFACTORING.md`.
