# Debugging und Incident-Runbooks

Diese Runbooks dokumentieren die Fehlerbilder, die beim Spring-Boot-Deployment
und beim Betrieb des Website-Servers tatsächlich aufgetreten sind. Sie sind
bewusst auf Diagnose und sichere nächste Schritte beschränkt; keine Anleitung
kopiert Secrets, Cookies oder Authorization-Header in Tickets.

## Schnelle Eingrenzung

Vom Ursprungssystem zuerst den interaktiven, redigierenden Collector verwenden:

```bash
./infrastructure/scripts/diagnostics/debug.sh
./infrastructure/scripts/diagnostics/debug.sh --area calendar --category http-500 --since 30m --tail 400
```

Er nutzt `.env.origin`, speichert die agententaugliche Ausgabe lokal unter
`.diagnostics/` und verändert das Zielsystem nicht. Direkte Zielserverbefehle
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
