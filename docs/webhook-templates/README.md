# Webhook-Templates

Dieses Verzeichnis enthält versionierte Vorlagen, die direkt in das Feld **Nachrichten-Template** im Staff-Panel kopiert werden können.

## Verwendung

1. Als Administrator **Staff-Panel → Discord-Webhooks** öffnen.
2. Das gewünschte Event auswählen.
3. Die gleichnamige Datei unter [`message-templates/`](message-templates/) öffnen.
4. Den vollständigen Dateiinhalt in **Nachrichten-Template** kopieren.
5. Testzustellung senden und die Darstellung im Ziel prüfen.

Die Vorlagen funktionieren für beide Zustellmodi:

- **Discord-Chat-Webhook:** Das Backend rendert die Vorlage und sendet die fertige Nachricht direkt an Discord.
- **Signierter JSON-Webhook:** Die Vorlage wird im Feld `destination.message_template` an den Bot oder Integrationsdienst übertragen. Der Empfänger entscheidet, ob und wie er sie rendert.

## Platzhalter

Gemeinsame Platzhalter:

- `{event}` – Event-Typ
- `{occurred_at}` – Zeitpunkt in UTC
- `{destination.name}` – Name des Webhook-Abonnements
- `{actor.display_name}` – Anzeigename des auslösenden Benutzers
- `{actor.username}` – Benutzername des Auslösers
- `{resource.type}` und `{resource.id}` – Ressourcentyp und ID
- `{resource.url}` – relativer Website-Pfad
- `{scope.type}`, `{scope.id}`, `{scope.fleet_id}`, `{scope.squad_id}` – Scope-Daten
- `{data.<feld>}` – ereignisspezifische Nutzdaten

Nicht vorhandene Platzhalter werden als leerer Text ausgegeben. Bedingte Abschnitte werden derzeit nicht unterstützt. Discord-Erwähnungen sind aus Sicherheitsgründen deaktiviert.

## Dateien

- [`all-message-templates.md`](all-message-templates.md) – alle Vorlagen in einem Dokument
- [`message-templates/`](message-templates/) – eine reine Textdatei pro Event zum direkten Kopieren
- [`signed-json-envelope.example.json`](signed-json-envelope.example.json) – Beispiel für den Payload eines signierten JSON-Webhooks

Die Dateinamen entsprechen exakt den Event-Typen aus dem Backend-Katalog. Die Repository-Prüfung stellt sicher, dass für jedes unterstützte Event genau eine Vorlage vorhanden ist.
