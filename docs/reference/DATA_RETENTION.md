# Datenaufbewahrung und Löschkonzept

Dieses Dokument beschreibt die technisch erzwungene Standardaufbewahrung. Abweichende gesetzliche
oder vertragliche Anforderungen müssen vor dem Produktivbetrieb durch den Verantwortlichen geprüft
und über die Spring-Konfiguration und Infrastruktur-Umgebungsdatei konfiguriert werden.

| Datenklasse | Standard | Zweck | Löschung |
|---|---:|---|---|
| Aggregierte IP-Sperrsignale | 7 Kalendertage | Ausschließlich Entscheidung über eine konkrete IP-Sperre | täglicher Maintenance-Lauf; sofort bei Sperrung |
| Abgelaufene/aufgehobene IP-Sperren | 90 Tage | Begrenzte Nachvollziehbarkeit der Zugriffskontrolle | täglicher Maintenance-Lauf |
| Audit-Historie | 365 Tage | Nachvollziehbarkeit administrativer Änderungen | täglicher Maintenance-Lauf |
| Discord-Webhook-Deliveries | 30 Tage | Zustellfehler, Wiederholung und Support | täglicher Maintenance-Lauf |
| Cookie-Einwilligungsentscheidungen | 400 Tage | Nachweis und Wiederherstellung der Auswahl | täglicher Maintenance-Lauf |
| Abgeschlossene Datenschutzanträge | 400 Tage | Nachweis von Export-, Berichtigungs- und Löschbearbeitung | täglicher Maintenance-Lauf; offene Anträge bleiben erhalten |
| Abgeschlossene Datenschutz-Kontakte | 400 Tage | Rückfragen und Nachweis der Bearbeitung | täglicher Maintenance-Lauf; offene Nachrichten bleiben bis zur Bearbeitung erhalten |
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

Die Ereignisse werden bereits beim Schreiben auf **Tagesebene aggregiert**. Pro IP,
Signalkategorie, Begründung, sicherem Ziel und UTC-Tag existiert höchstens ein Datensatz mit:

- normalisierter einzelner IP-Adresse,
- UTC-Kalendertag,
- einer der oben genannten groben Signalkategorien,
- einer festen Begründung wie abgelehnte Anmeldung, überschrittenes Rate-Limit oder verdächtiger Scan,
- bei bekannten API-Endpunkten dem normalisierten Spring-Routen-Template ohne konkrete Objekt-IDs oder bei
  Scans einer festen Zielkategorie wie „Git-Metadaten“ oder „Umgebungsdatei“,
- Tageszähler der Signale.

Nicht gespeichert werden freie oder nicht zugeordnete Request-Pfade, Query-String, User-Agent,
Referrer, Request-ID, HTTP-Methode,
Request-/Response-Inhalt, Statusdetails, Laufzeit, Accountname, genauer Request-Zeitpunkt, Exception
oder Stacktrace. Die Admin-Webseite liefert ausschließlich diese Aggregationen pro IP und Tag
einschließlich Begründung und sicherem Routen-/Scan-Ziel.
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
resolved_privacy_request_retention_days = 400
pending_registration_retention_days = 30
reviewed_registration_retention_days = 90
interval_hours = 24
```

Eine Verkürzung ist grundsätzlich vorzuziehen. Eine Verlängerung braucht einen dokumentierten Zweck,
eine Rechtsgrundlage und einen Termin zur erneuten Prüfung. Änderungen wirken beim nächsten
Maintenance-Lauf; vor einer deutlichen Verkürzung ist ein kontrolliertes Backup sinnvoll.

## Nicht automatisch gelöschte Inhalte

Forumbeiträge, Guides, Builds und andere veröffentlichte fachliche Inhalte können Referenzen und
berechtigte Interessen weiterer Community-Mitglieder berühren. Bei einer bestätigten Accountlöschung
bleiben solche Inhalte deshalb unter einer neutralen, nicht mehr anmeldbaren Identität erhalten.
Profil, Präferenzen, Sessions, Flotten- und Gruppenmitgliedschaften sowie Abstimmungen werden
entfernt; nullable Erstellerbezüge werden entkoppelt.

## Betroffenenworkflow

Im Profil steht ein maschinenlesbarer JSON-Export bereit. Er enthält Account- und Profildaten,
Einwilligungen, Mitgliedschaften und selbst erstellte Inhalte, aber keine Passwort-, Session- oder
Consent-Schlüssel und keine Daten anderer Nutzer.

Direkt änderbare Profildaten werden ohne Antrag über den Profileditor berichtigt. Für nicht direkt
änderbare Daten kann ein formaler Berichtigungsantrag gestellt werden. Löschanträge erfordern die
erneute Eingabe des Benutzernamens und werden erst nach administrativer Identitäts- und
Folgenprüfung ausgeführt. Bootstrap-Administratoren sind aus Gründen der Betriebsfähigkeit von der
Accountlöschung ausgeschlossen.

Admins bearbeiten offene Vorgänge unter `/admin/privacy-requests`. Entscheidung, Bearbeiter,
Zeitpunkt und Begründung werden am Antrag gespeichert und zusätzlich im Audit-Log protokolliert.

Die öffentliche Route `/privacy` stellt die Cookie-Einstellungen, eine verständliche Übersicht der
Verarbeitung und ein datensparsames Kontaktformular bereit. Das Formular speichert keine IP-Adresse
und keinen User-Agent. E-Mail-Adresse und Nachrichteninhalt verbleiben in der Anwendung und werden
nicht über Discord-Webhooks versendet; Administratoren bearbeiten sie im Datenschutz-Postfach.
