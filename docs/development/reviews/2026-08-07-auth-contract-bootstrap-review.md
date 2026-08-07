# Auth- und API-Vertragsprüfung vom 7. August 2026

## Anlass

Nach dem Spring-Layer-/DTO-Umbau lieferte die produktive Anmeldung mit den
vermeintlichen First-Run-Zugangsdaten HTTP 401. Deshalb wurde die komplette
Kette vom Browserrequest über OpenAPI, generierte DTOs und Controller bis zur
Bootstrap-Initialisierung und Passwortprüfung erneut geprüft.

## Ergebnis der Login-Prüfung

Der Login-Request war bereits synchron: Frontend, `LoginRequest`, generiertes
`AuthApi`, `AuthController` und `AuthService` verwenden durchgehend die Felder
`username` und `password`. Die Passwortprüfung unterstützt außerdem das beim
vorherigen Backend verwendete PBKDF2-Format. Der PostgreSQL-Integrationstest
meldet einen frisch erzeugten Bootstrap-Administrator erfolgreich mit dem
konfigurierten First-Run-Passwort an.

Ein 401 mit einem vorhandenen Datenbestand bedeutet deshalb nicht, dass das
Login-DTO vertauscht ist. `SEED_ADMIN_PASSWORD` ist absichtlich nur das Secret
für die erstmalige Benutzeranlage. Existiert bereits ein Bootstrap-Admin, wird
sein aktueller Passwort-Hash bei Neustarts und Deployments nicht aus der
Environment-Datei überschrieben.

## Gefundener Vertragsdrift

Der OpenAPI-Vertrag enthielt noch das alte generische Validation-Fehlerformat:
172 Operationen dokumentierten HTTP 422 mit einer strukturierten
`HTTPValidationError`-Antwort, obwohl Spring Bean-Validation und Bindingfehler
HTTP 400 mit einem öffentlichen `detail`-Text zurückgeben. Der Login dokumentierte
außerdem seinen realen HTTP-401-Fall nicht.

Der Vertrag verwendet nun `ApiError` mit `detail` als gemeinsame öffentliche
Fehlerrepräsentation. Die 172 generischen Validation-Responses sind HTTP 400.
HTTP 422 bleibt nur bei sechs fachlich semantischen Prüfungen explizit erhalten.
`POST /api/auth/login` dokumentiert 200, 400 und 401 mit den tatsächlich
verwendeten Schemas.

## First-Run-Invariante

Frische Installationen verifizieren die generierten
`SEED_ADMIN_USERNAME`/`SEED_ADMIN_PASSWORD` nach Readiness über die öffentliche
Login-API. Ein abweichender Benutzer oder Passwort-Hash bricht die Aktivierung
ab. Updates bestehender Installationen führen diese Prüfung nicht aus, damit ein
später geändertes Administratorpasswort niemals gegen das alte Seed-Secret
getestet oder zurückgesetzt wird.

## Release-Baseline

Nach dem Architektur-Cutover wird die Produktversion bewusst auf `1.0.0`
zurückgesetzt. Maven-, Frontend-, OpenAPI-, Referenz- und Deploymentversion sind
wieder an dieser gemeinsamen Basis ausgerichtet. Weitere kompatible Fixes starten
bei `1.0.1`.
