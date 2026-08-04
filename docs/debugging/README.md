# Debugging und Incident-Runbooks

Diese Runbooks dokumentieren die Fehlerbilder, die beim Spring-Boot-Deployment
und beim Betrieb des Website-Servers tatsächlich aufgetreten sind. Sie sind
bewusst auf Diagnose und sichere nächste Schritte beschränkt; keine Anleitung
kopiert Secrets, Cookies oder Authorization-Header in Tickets.

## Schnelle Eingrenzung

```bash
sudo systemctl status rbf-hub.service --no-pager
sudo journalctl -u rbf-hub.service -n 200 --no-pager
sudo /opt/rbf/current/infrastructure/scripts/services/status.sh
sudo /opt/rbf/current/infrastructure/scripts/checks/doctor.sh
sudo /opt/rbf/current/infrastructure/scripts/services/logs.sh api gateway
```

Bei einem fehlgeschlagenen Release zuerst die Aktivierungsdiagnose unter
`/opt/rbf/shared/deployments/failed-*.log` sichern. Container und Netzwerke erst
danach bereinigen; die Diagnose darf nicht durch `docker compose down` verloren
gehen.

Die ausführliche Sammlung steht in
[`DEPLOYMENT_INCIDENTS.md`](DEPLOYMENT_INCIDENTS.md).
