# Entwicklung

## Backend

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.lock
pip install --no-deps -e .
cp .env.example .env
rbf-dev
```

SQLite ist der lokale Standard. Produktionslogik verweigert SQLite und verlangt PostgreSQL plus
`DB_SCHEMA_MODE=migrate`.

## Frontend

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

Node 22 und Python 3.12 entsprechen der CI. Das Lockfile muss ausschließlich öffentliche
Registry-URLs enthalten.

## Befehle

```bash
make test       # Ruff, Backendtests, Build-Designer- und Locale-Checks
make test-full  # zusätzlich Migration, Produktionsbuild und Infrastruktur
make validate             # Release-Invarianten plus vollständige Tests
make clean                # generierte Dateien und Buildausgaben entfernen
make clean-all            # zusätzlich lokale Abhängigkeitsumgebungen entfernen
make check-tree           # sauberen, paketfreien Repository-Baum prüfen
make build-recovery-linux # Linux-Recovery-Binary, Installer und DEB bauen
```

Neue API-Funktionen benötigen Berechtigungs-, Erfolgs- und Fehlerfall. Komplexe reine Berechnungen
werden ohne Browser oder Datenbank getestet. UI-End-to-End-Tests werden erst ergänzt, wenn ein
kritischer Ablauf nicht zuverlässig durch Service- und Komponentenlogik abgedeckt werden kann.

## Abhängigkeiten

`requirements.lock` bildet die Produktionsumgebung ab, `requirements-dev.lock` ergänzt die Testwerkzeuge. Änderungen an `pyproject.toml` müssen beide Lockfiles bewusst aktualisieren.
