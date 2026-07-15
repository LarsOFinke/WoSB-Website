# Discord-Webhooks und signierte Integrationen

Die Webhook-Verwaltung ist im Staff-Panel unter **Discord-Webhooks** erreichbar und vollständig von der Seite **Discord-Bot** getrennt. Beide Bereiche funktionieren unabhängig voneinander.

## Zustellmodi

### Discord-Chat-Webhook

Das Backend sendet eine fertige Discord-Nachricht direkt an einen nativen Discord-Channel-Webhook. Dafür wird weder der Discord-Bot noch dessen Repository benötigt. Die Webhook-URL wird nach dem Speichern maskiert.

### Signierter JSON-Webhook

Das Backend sendet ein strukturiertes Event an den Discord-Bot oder einen anderen Integrationsdienst. Der Empfänger übernimmt Routing, Deduplizierung und Darstellung.

## Vorlagen

Direkt kopierbare **englische** Nachrichtenvorlagen für alle unterstützten Events liegen unter [`docs/webhook-templates/`](webhook-templates/). Die Dateien unter `message-templates/` enthalten ausschließlich den Text, der in das Staff-Panel eingefügt wird. Die erweiterten Vorlagen enthalten Ereignisdetails und anklickbare Links zu Builds, Guides, Forenbeiträgen, Squads, Kalender und Registrierungsverwaltung.

Beim Discord-Chat-Webhook rendert das Backend die Vorlage. Beim signierten JSON-Webhook wird sie unverändert als `destination.message_template` übertragen. Relative Ressourcenpfade werden im Envelope gegen die erste HTTP(S)-Origin aus `CORS_ORIGINS` qualifiziert, sodass `{resource.url}` in Discord und externen Integrationen als vollständiger Link verfügbar ist.

## Signierte Zustellung

Jede signierte Zustellung ist ein HTTP-`POST` mit JSON-Body und folgenden Headern:

- `Content-Type: application/json; charset=utf-8`
- `X-RBF-Event`: Event-Typ
- `X-RBF-Delivery`: eindeutige Zustellungs-ID
- `X-RBF-Timestamp`: Unix-Zeitstempel für Replay-Schutz
- `X-RBF-Signature`: `sha256=<hex digest>`

Die Signatur ist ein HMAC-SHA256-Digest des exakten Request-Bodys mit dem nach Erstellung oder Rotation angezeigten Secret.

```python
import hashlib
import hmac


def verify_webhook(raw_body: bytes, signature_header: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

Der Empfänger sollte zusätzlich Zeitstempel außerhalb einer kurzen Toleranz ablehnen und `X-RBF-Delivery` speichern, um Wiederholungen zu verhindern.

## Payload-Envelope

Ein vollständiges Beispiel liegt unter [`webhook-templates/signed-json-envelope.example.json`](webhook-templates/signed-json-envelope.example.json).

`channel_key` ist absichtlich keine Discord-Channel-ID. Es ist ein stabiler Routing-Key wie `registrations`, `events` oder `squads`, den der externe Empfänger auf sein eigenes Ziel abbildet.

## Testzustellungen und reale Ereignisse

Der Button **Test senden** verwendet das erste ausgewählte Event des Abonnements und erzeugt dafür einen realistischen Vorschau-Payload. Damit werden Ziel-URL, Discord-Darstellung, Template-Platzhalter und Transport geprüft. Die Testzustellung ersetzt jedoch keinen echten Fachvorgang: Sie wird direkt für das ausgewählte Abonnement erzeugt und beweist daher nicht, dass ein späteres Ereignis fachlich zum Fleet-/Squad-Scope passt.

Bei einem echten Vorgang muss in der Zustellhistorie eine neue Zeile mit dem tatsächlichen Event-Typ erscheinen. Fehlt diese Zeile vollständig, wurde das Ereignis nicht für das Abonnement eingeplant, beispielsweise wegen abweichendem Event-Typ, inaktivem Abonnement oder nicht passendem Scope. Eine vorhandene Zeile mit `failed` bedeutet dagegen, dass das Ereignis eingeplant wurde, aber der externe Transport fehlgeschlagen ist.

## Zustellverhalten

- Events und Zustellversuche werden vor dem Versand gespeichert.
- Zustellungen laufen nach der API-Antwort als FastAPI-Hintergrundaufgabe.
- Erfolge und Fehler sind im Staff-Panel sichtbar.
- Fehlgeschlagene Zustellungen können manuell wiederholt werden.
- Jedes Abonnement unterstützt eine Testzustellung.
- Secrets werden nur nach Erstellung oder Rotation vollständig angezeigt.
- Produktionsziele müssen HTTPS verwenden.

## Container-Netzwerk und DNS

Ausgehende Zustellungen werden vom Compose-Service `api` gesendet. Der Service besitzt neben dem internen Datenbanknetz ein eigenes Outbound-Netz für DNS und HTTPS.

```bash
docker compose -f infrastructure/compose.yml ps

docker compose -f infrastructure/compose.yml exec -T api \
  python - <<'PY'
import socket
print(socket.getaddrinfo("discord.com", 443))
PY
```

Nach Änderungen am Netzwerk den API-Container neu erstellen:

```bash
./update.sh
```
