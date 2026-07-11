# Build-Designer-Katalog, Cookie-Einwilligung und Asset-Fixes

## Enthaltene Änderungen

### Build-Designer

- Segel- und Laternen-Dropdowns enthalten keine Stat-Zusatzzeile mehr.
- Laternen können nach einer Auswahl wieder gewechselt oder entfernt werden.
- Absolute Geschwindigkeitsboni in Knoten werden getrennt von Prozentboni berechnet.
- Überfallsegel verwenden den gemeldeten Tooltip-Wert `+4,1 kn` und `-20 % cruising speed gain`.
- Ungeprüfte frühere Segel-/Laternenannahmen wurden entfernt.
- Die Forschungsbelohnung für Slot 5 wendet ihre sechs `-10 %`-Mali automatisch an.
- Der Spezialistenkatalog enthält 24 stabile Seed-Einträge und bleibt über die Stammdatenverwaltung erweiterbar.

### Cookie-Einwilligung

Neue API-Endpunkte:

```text
GET  /api/privacy/cookie-policy
GET  /api/privacy/cookie-consent
POST /api/privacy/cookie-consent
```

Entscheidungen werden append-only in `cookie_consent_decisions` gespeichert. Ein zufälliger, technisch notwendiger HttpOnly-Cookie verbindet den Browser mit seiner jeweils neuesten Entscheidung. Gespeichert werden Policy-Version, optionale Kategorien, Nutzerbezug sofern angemeldet und Zeitstempel.

Kategorien:

- technisch notwendig
- Präferenzen
- Analyse
- externe Medien

Optionale Kategorien starten deaktiviert. Im Footer lässt sich die Auswahl später erneut öffnen. Der Code ist eine technische Datenschutzgrundlage, ersetzt aber keine Prüfung der final angebundenen Dienste und Datenschutzerklärung.

### Konsolen-/Assetfehler

- Favicon/OG-Icon wird über `/rbf-fleet-icon.png` aus dem öffentlichen Root ausgeliefert.
- Der Slot-Platzhalter wird als Vite-Asset importiert und erhält beim Build einen gehashten `/assets/...`-Pfad.
- Alte absolute Referenzen auf `/branding/...` und `/icons/...` wurden aus dem aktiven Frontend entfernt.

`Unchecked runtime.lastError: The message port closed before a response was received` stammt typischerweise aus Browser-Erweiterungs-Messaging. Die Anwendung verwendet keine Browser-Extension-API; der Fehler lässt sich daher nicht aus dem Webseiten-Code heraus abfangen.

## Datenbank

Migration:

```text
d4e5f6a7b8c9_cookie_consent.py
```

Die Tabelle ist normalisiert und enthält keine duplizierten Kategorien- oder Nutzerprofile. Einwilligungsänderungen werden als neue Entscheidungen gespeichert, damit der Verlauf nachvollziehbar bleibt.

## Validierung

- Backend-Testlauf: 51 Tests
- frische Alembic-Migration bis Head
- vollständiger Seed zweimal hintereinander
- 24 aktive Spezialisten nach Seed
- Locale-Prüfung für sieben Sprachen
- Build-Designer-Regressionsprüfung
- Vite-Produktionsbuild
- gezielter Ruff-Check aller neu geänderten Python-Dateien
