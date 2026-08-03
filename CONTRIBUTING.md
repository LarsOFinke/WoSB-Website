# Beitragen

Für alle Beiträge gelten [die Qualitätsstandards](docs/development/QUALITY_STANDARDS.md) und der
[Repository-Arbeitsleitfaden](AGENTS.md).

1. Kleine, fachlich abgeschlossene Änderungen bevorzugen.
2. Datenbankschema ausschließlich über Alembic ändern.
3. Stammdaten über stabile `seed_id`, Revision und Checksumme pflegen.
4. API-Berechtigungen immer serverseitig testen; Frontend-Guards sind nur Komfort.
5. Keine neue große Seite oder Service-Datei ohne klaren Grund. Ab etwa 300–400 Zeilen prüfen, ob
   Datenkatalog, Berechnung, API-Zugriff oder UI-Abschnitt eine eigene Verantwortung ist.
6. Vor dem Pull Request ausführen:

```bash
make validate
```

Commits und Pull Requests sollen Problem, Lösung, Migration/Seed-Auswirkung und Testnachweis nennen.
