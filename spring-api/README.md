# RBF Secure API

Dieser Dienst ist der zentrale HTTP-Einstiegspunkt der schrittweisen
Backend-Migration. Authentifizierung ist nativ in Spring implementiert; noch nicht
migrierte Fachrouten werden intern an FastAPI weitergereicht.

Nativ besitzt Spring aktuell:

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/change-password`
- `GET /api/auth/me`
- `GET /api/legal-notice`

Alle `/api/**`-Routen werden durch Spring geschützt und angenommen. Nicht migrierte
Fachrouten laufen ausschließlich über den internen Proxy zu FastAPI; der Browser und
NGINX sprechen nicht mehr direkt mit dem FastAPI-Container. `/uploads/...` bleibt als
kompatibler Legacy-Dateipfad zunächst direkt am API-Container.

## Lokal prüfen

Voraussetzungen sind JDK 21 und Maven 3.9 oder neuer.

```bash
mvn --batch-mode --no-transfer-progress test
```

Für einen lokalen Start werden `SPRING_DATASOURCE_URL`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, `SESSION_COOKIE_SECURE`, `ALLOWED_HOSTS` und `CORS_ORIGINS`
benötigt. Hibernate darf das von Alembic verwaltete Schema nur validieren und nie
erzeugen oder verändern.

## Sicherheitsvertrag

- PBKDF2-HMAC-SHA256 und SHA-256-Sessionhashes bleiben kompatibel zum Python-Bestand.
- Cookies sind HttpOnly, im Produktionsprofil Secure und haben eine explizite SameSite-Policy.
- Host- und Origin/Sec-Fetch-Prüfung weisen fremde Werte ab; NGINX begrenzt Anfrageraten.
- Der Actuator veröffentlicht ausschließlich Health und bleibt im internen Compose-Netz.
- Der Container läuft ohne root, Linux-Capabilities oder allgemeines Outbound-Netz.
