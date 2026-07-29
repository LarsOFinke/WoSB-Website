# Datenaufbewahrung und Löschkonzept

Dieses Dokument beschreibt die technisch erzwungene Standardaufbewahrung. Abweichende gesetzliche
oder vertragliche Anforderungen müssen vor dem Produktivbetrieb durch den Verantwortlichen geprüft
und über `backend/config/uploads.cfg` konfiguriert werden.

| Datenklasse | Standard | Zweck | Löschung |
|---|---:|---|---|
| Aggregierte IP-Sperrsignale | 7 Kalendertage | Ausschließlich Entscheidung über eine konkrete IP-Sperre | täglicher Maintenance-Lauf; sofort bei Sperrung |
| Abgelaufene/aufgehobene IP-Sperren | 90 Tage | Begrenzte Nachvollziehbarkeit der Zugriffskontrolle | täglicher Maintenance-Lauf |
| Audit-Historie | 365 Tage | Nachvollziehbarkeit administrativer Änderungen | täglicher Maintenance-Lauf |
| Discord-Webhook-Deliveries | 30 Tage | Zustellfehler, Wiederholung und Support | täglicher Maintenance-Lauf |
| Cookie-Einwilligungsentscheidungen | 400 Tage | Nachweis und Wiederherstellung der Auswahl | täglicher Maintenance-Lauf |
| Offene Registrierungsanträge | 30 Tage | Accountprüfung | täglicher Maintenance-Lauf |
| Geprüfte Registrierungsanträge | 90 Tage | Nachvollziehbarkeit der Entscheidung | täglicher Maintenance-Lauf |
| Abgelaufene Sessions | bis Ablaufzeitpunkt | Anmeldung und Sicherheit | täglicher Maintenance-Lauf |

Passworthashes in Registrierungsanträgen werden direkt nach Genehmigung oder Ablehnung überschrieben.
Genehmigte Accounts behalten ausschließlich den Hash im eigentlichen Benutzerkonto.

## Zweckgebundene IP-Sperrsignale

Die Anwendung führt **keine allgemeine Request- oder Besucherprotokollierung** in der Datenbank.
Gespeichert werden nur folgende grobe Ereigniskategorien, wenn sie für eine IP-Sperrentscheidung
relevant sind:

- verdächtige Scan-/Reconnaissance-Versuche,
- fehlgeschlagene Anmeldungen,
- Rate-Limit-Treffer.

Die Ereignisse werden bereits beim Schreiben auf **Tagesebene aggregiert**. Pro IP, Signalkategorie und UTC-Tag existiert höchstens ein Datensatz mit:

- normalisierter einzelner IP-Adresse,
- UTC-Kalendertag,
- einer der oben genannten groben Signalkategorien,
- Tageszähler der Signale.

Nicht gespeichert werden Route, Query-String, User-Agent, Referrer, Request-ID, HTTP-Methode,
Request-/Response-Inhalt, Statusdetails, Laufzeit, Accountname, genauer Request-Zeitpunkt, Exception
oder Stacktrace. Die Admin-Webseite liefert ausschließlich diese Aggregationen pro IP und Tag.
Einzelereignisse oder Rohlogs existieren weder in der Datenbank noch über eine API.

Wird eine IP gesperrt, werden ihre temporären Sperrsignale in derselben Datenbanktransaktion sofort
gelöscht. Die aktive Sperre behält die exakte IP nur so lange, wie sie für die Zugriffskontrolle
benötigt wird. Abgelaufene oder aufgehobene Sperren werden nach der begrenzten Historienfrist gelöscht.
Audittexte enthalten keine Kopie der IP-Adresse.

## Infrastruktur-Logs

Der produktive NGINX-Gateway schreibt keine Access-Logs. Damit werden dort insbesondere keine
Routen, IP-Adressen oder User-Agents als normale Besuchsprotokolle aufgezeichnet. Das Backend-
Konsolenlogging enthält keine Client-IP, Route, Query oder User-Agent. Kritische Betriebsfehler sind
von der bannbezogenen Datenbankauswertung getrennt und werden nicht auf der Webseite angezeigt.

## Konfiguration

```ini
[maintenance]
security_event_retention_days = 7
inactive_ip_block_retention_days = 90
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
