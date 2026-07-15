# Refactoring-Notizen

## Ziele

- KISS: kleine Module, wenig impliziter Zustand und keine zusätzliche Framework-Schicht
- SRP: Laden, Parsen, Validieren, Mapping, Persistenz und Transport sind getrennt
- OCP/DIP: externe Abhängigkeiten wie Webhook-Transport und Session-Factory sind injizierbar
- Kompatibilität: bestehende API-Routen und öffentliche Service-Funktionen bleiben erhalten

## Wesentliche Änderungen

- `config/app.toml` wurde durch fachlich getrennte `.cfg`-Dateien ersetzt.
- `core/config.py` wurde von 235 Zeilen auf eine kleine Kompatibilitätsfassade reduziert.
- Konfigurationsmodelle sind immutable und nach Anwendung, Datenbank, Storage, Logging,
  Session, Seeds und Upload-Limits gruppiert.
- App-Erzeugung, Logging, Datenbanksessions, Runtime-Pfade, Passwort-Hashing und
  Passwort-Policy besitzen explizite Klassen.
- Die größten fachlichen Services wurden zerlegt, ohne ihre bisherigen Imports zu brechen.
- Request-IP-Ermittlung und Log-Entscheidungen sind eigenständig testbare Policies.

## Erweiterungsregel

Eine neue Einstellung erhält zunächst ein Modellfeld und einen fachlichen Reader. Eine neue
Integration erhält einen Port/Transport und einen koordinierenden Service. Router dürfen
keine Persistenz-, Mapping- oder Validierungsdetails aufnehmen.
