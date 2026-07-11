# RBF Backend

FastAPI-Anwendung mit SQLAlchemy 2, Alembic und fachlich getrennten Modulen.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.lock
pip install --no-deps -e .
cp .env.example .env
rbf-dev
```

Die vollständige Testbasis wird vom Repository-Root über `make test` ausgeführt; der isolierte
Runner verhindert, dass globale App-/SQLAlchemy-Zustände zwischen Modulen lecken. Produktion nutzt
ausschließlich PostgreSQL, Alembic und explizite System-/Stammdaten-Seeds.

Siehe `../docs/ARCHITECTURE.md`, `../docs/DATABASE.md` und `../docs/TESTING.md`.
