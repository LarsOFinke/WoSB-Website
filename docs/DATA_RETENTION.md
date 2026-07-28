# Datenaufbewahrung und Löschkonzept

Dieses Dokument beschreibt die technisch erzwungene Standardaufbewahrung. Abweichende gesetzliche
oder vertragliche Anforderungen müssen vor dem Produktivbetrieb durch den Verantwortlichen geprüft
und über `backend/config/uploads.cfg` konfiguriert werden.

| Datenklasse | Standard | Zweck | Löschung |
|---|---:|---|---|
| Anwendung-/Request-Logs | 30 Tage | Fehleranalyse, Missbrauchserkennung | täglicher Maintenance-Lauf |
| Audit-Historie | 365 Tage | Nachvollziehbarkeit administrativer Änderungen | täglicher Maintenance-Lauf |
| Discord-Webhook-Deliveries | 30 Tage | Zustellfehler, Wiederholung und Support | täglicher Maintenance-Lauf |
| Cookie-Einwilligungsentscheidungen | 400 Tage | Nachweis und Wiederherstellung der Auswahl | täglicher Maintenance-Lauf |
| Offene Registrierungsanträge | 30 Tage | Accountprüfung | täglicher Maintenance-Lauf |
| Geprüfte Registrierungsanträge | 90 Tage | Nachvollziehbarkeit der Entscheidung | täglicher Maintenance-Lauf |
| Abgelaufene Sessions | bis Ablaufzeitpunkt | Anmeldung und Sicherheit | täglicher Maintenance-Lauf |

Passworthashes in Registrierungsanträgen werden direkt nach Genehmigung oder Ablehnung überschrieben.
Genehmigte Accounts behalten ausschließlich den Hash im eigentlichen Benutzerkonto.

Request-Logs speichern den normalisierten Client-IP-Wert, User-Agent, Route, Status und Dauer.
Query-Parameterwerte werden vollständig entfernt; lediglich Parameternamen bleiben für die Diagnose
erhalten. Rohe Proxy-Ketten werden nicht persistiert.

## Konfiguration

```ini
[maintenance]
app_log_retention_days = 30
audit_log_retention_days = 365
webhook_delivery_retention_days = 30
cookie_consent_retention_days = 400
pending_registration_retention_days = 30
reviewed_registration_retention_days = 90
interval_hours = 24
```

Eine Verkürzung ist grundsätzlich vorzuziehen. Eine Verlängerung braucht einen dokumentierten Zweck,
eine Rechtsgrundlage und einen Termin zur erneuten Prüfung. Änderungen wirken beim nächsten
Maintenance-Lauf; vor einer deutlichen Verkürzung ist ein kontrolliertes Backup sinnvoll.

## Nicht automatisch gelöschte Inhalte

Benutzerkonten, Flottenmitgliedschaften, Forumbeiträge, Guides, Builds und Uploads sind fachliche
Inhalte. Ihre Löschung erfordert eine bewusste Moderations- oder Betroffenenanfrage, damit Referenzen,
Urheberschaft und öffentliche Inhalte korrekt behandelt werden. Bis ein Self-Service-Verfahren
existiert, werden Auskunft, Export, Berichtigung und Löschung organisatorisch durch Administratoren
bearbeitet und im Audit-Log dokumentiert.
