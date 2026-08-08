# Debugging und Incident-Runbooks

Diese Runbooks dokumentieren die Fehlerbilder, die beim Spring-Boot-Deployment
und beim Betrieb des Website-Servers tatsächlich aufgetreten sind. Sie sind
bewusst auf Diagnose und sichere nächste Schritte beschränkt; keine Anleitung
kopiert Secrets, Cookies oder Authorization-Header in Tickets.

- [Modulorientiertes Debugging](MODULE_DEBUGGING.md) – Schichtentrennung,
  Evidenzminimum und passende Regressionstest-Ebene
- [Deployment-Incidents](DEPLOYMENT_INCIDENTS.md) – bekannte konkrete Symptome,
  Ursachen und sichere nächste Schritte
- [Legacy-Build-Datenmigration](LEGACY_BUILD_DATA_MIGRATION.md) – geprüfter
  Build-only Python→Java-Teilrestore mit Dry-Run, semantischer FK-Auflösung und
  Test→Production-Promotion

## Schnelle Eingrenzung

Vom Ursprungssystem zuerst den interaktiven, redigierenden Collector verwenden:

```bash
./infrastructure/scripts/diagnostics/debug.sh
./infrastructure/scripts/diagnostics/debug.sh --area calendar --category http-500 --since 30m --tail 400
```

Ohne Flag nutzt er `.env.origin.test`; Production wird nur mit
`--production` und `.env.origin.production` ausgewählt. Die agententaugliche
Ausgabe landet lokal unter `.diagnostics/` und verändert das Zielsystem nicht.
Direkte Zielserverbefehle
sind nur der manuelle Fallback:

```bash
sudo systemctl status rbf-hub.service --no-pager
sudo journalctl -u rbf-hub.service -n 200 --no-pager
sudo /srv/rbf/current/infrastructure/scripts/services/status.sh
sudo /srv/rbf/current/infrastructure/scripts/checks/doctor.sh
sudo /srv/rbf/current/infrastructure/scripts/services/logs.sh api gateway
```

Bei einem fehlgeschlagenen Release zuerst die Aktivierungsdiagnose unter
`/srv/rbf/shared/deployments/failed-*.log` sichern. Container und Netzwerke erst
danach bereinigen; die Diagnose darf nicht durch `docker compose down` verloren
gehen.

Die ausführliche Sammlung steht in
[`DEPLOYMENT_INCIDENTS.md`](DEPLOYMENT_INCIDENTS.md).
