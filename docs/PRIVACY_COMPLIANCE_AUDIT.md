# Dreifachprüfung Datenschutz-Compliance

Stand: 2. August 2026

Diese technische Prüfung ersetzt keine Rechtsberatung. Sie bewertet Implementierung und
Repository-Konfiguration; Verantwortlicher, tatsächlicher Serverbetrieb, Verträge und die
veröffentlichte Datenschutzerklärung müssen organisatorisch bestätigt werden.

## Ergebnis

Die technischen Datenschutzfunktionen sind umgesetzt und automatisiert prüfbar. Eine rechtliche
Gesamtfreigabe ist erst möglich, wenn die Betreiberangaben, Rechtsgrundlagen, Empfänger,
Drittlandtransfers und tatsächlichen Fristen in der produktiven Datenschutzerklärung bestätigt sind.

## Kontrolle 1: Rechts- und Transparenzabgleich

- Datenminimierung, Zweckbindung und Speicherbegrenzung werden über kleine API-Verträge,
  deaktivierte Access-Logs und `DATA_RETENTION.md` umgesetzt.
- First-Party-Session- und Consent-Cookies sind HttpOnly, in Produktion Secure und SameSite-
  geschützt. Optionale Kategorien sind standardmäßig abgelehnt und können gleichwertig abgelehnt
  oder später über Footer und `/privacy` geändert werden.
- Es ist derzeit kein Analyse-, Werbe- oder externes Medien-Tracking angebunden. Sprache und bewusst
  gewählte Oberflächeneinstellungen werden lokal als funktionale Präferenz gespeichert.
- `/privacy` erklärt Verarbeitung, Cookies, Empfänger, Löschung und Kontaktmöglichkeiten sichtbar.
  Die rechtlich vollständige Art.-13/14-Erklärung bleibt ein Go-live-Gate des Verantwortlichen.

Maßstab: Art. 5, 12–17, 20, 25 und 32 DSGVO sowie § 25 TDDDG. Technisch notwendige
Endgerätespeicherung ist nur für den ausdrücklich gewünschten Dienst zulässig; zukünftige Analytics-
oder Drittmedienintegration darf erst nach wirksamer Einwilligungsanbindung aktiviert werden.

## Kontrolle 2: Datenmodell und Datenflüsse

- Personenbezogene Tabellen, Benutzer-Fremdschlüssel, Klartext-Identifikatoren und Exporte wurden
  gegen die SQLAlchemy-Metadaten geprüft.
- Der Export enthält die dem Nutzer zugeordneten Account-, Profil-, Consent-, Mitgliedschafts-,
  Inhalts-, Datei-, Kontakt- und Antragsdaten; Passwort-, Token- und Consent-Schlüssel bleiben aus
  Sicherheitsgründen ausgeschlossen.
- Der freigegebene Löschservice widerruft Sessions, entfernt Profil/Präferenzen/Mitgliedschaften/
  Votes, entkoppelt nullable Urheberbezüge, redigiert Audit- und Kontaktdaten und deaktiviert den
  pseudonymisierten Restaccount in einer Transaktion.
- Nicht pauschal löschbare Community-Inhalte bleiben nur nach menschlicher Rechte- und
  Folgenprüfung erhalten. Personenbezogene Inhalte im Freitext sind im Einzelfall zu löschen oder
  zu anonymisieren; diese Abwägung darf nicht blind automatisiert werden.
- Datenschutzkontakte speichern ausschließlich Antwortadresse, Betreff, Nachricht, Status und
  Bearbeitung. Keine IP, kein User-Agent und kein Nachrichteninhalt gelangen in Webhooks.

## Kontrolle 3: Ausführbare Nachweise

Verbindliche Regressionstests prüfen:

- Cookie-Default, Ablehnung, Änderung, Policy-Version und Cookie-Flags,
- Export ohne Authentisierungsgeheimnisse,
- Identitätsbestätigung und Admin-Grenze für Löschanträge,
- transaktionale Pseudonymisierung und Session-/Profildatenentfernung,
- Kontaktformular, Honeypot, Admin-Inbox und Bearbeitung,
- automatische Löschung aller dokumentierten operativen Datenklassen,
- Zugriffsschutz für Moderatoren und nicht angemeldete Besucher.

Release-Gates bleiben `make validate`, Alembic Upgrade/Check, Security-Audit und die PostgreSQL-
Recovery-Matrix.

## Sicher automatisiert versus menschliches Gate

Automatisiert sind Fristen, Sessionwiderruf, relationale Löschmatrix, Pseudonymisierung, Export und
Nachweis. Nicht automatisiert werden Identitätsprüfung, gesetzliche Aufbewahrungsausnahmen und die
Abwägung fremder Rechte an Community-Inhalten. Eine sofortige Löschung allein nach Browserklick
wäre bei Accountübernahme irreversibel und ist daher bewusst ausgeschlossen.

## Verbleibende Go-live-Pflichten

1. Verantwortlichen und Datenschutzkontakt mit echten Angaben veröffentlichen.
2. Zwecke und Rechtsgrundlagen je Datenklasse bestätigen; berechtigte Interessen dokumentieren.
3. Discord/Raid-Helper als Empfänger, Auftrags-/Drittlandkontext und aktivierte Ereignisse prüfen.
4. Lösch- und Auskunftsfristen organisatorisch überwachen und Identitätsprüfung dokumentieren.
5. Backup-Rotation testen: Produktivdaten verschwinden nach Ablauf aus allen Backupgenerationen;
   ein Restore muss nachträgliche Löschungen erneut anwenden.
6. Verzeichnis der Verarbeitungstätigkeiten, TOMs und gegebenenfalls AV-Verträge pflegen.
