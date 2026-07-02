# WoSB Gruppenmanagement – Backend Blueprint

FastAPI-Backend für die WoSB-Gruppenmanagement-Webseite auf Basis von SQLAlchemy 2.x und SQLite als lokaler Standarddatenbank. Die Python-Abhängigkeiten werden über `pyproject.toml` verwaltet.

## Wichtig in diesem Stand

- signierte Bearer-Tokens statt Frontend-only-Auth-Placeholder,
- `GET /api/v1/auth/me` validiert die aktuelle Session serverseitig,
- Benutzerrollen `member` und `admin`,
- Gruppen- und Build-Listen sind öffentlich lesbar, Schreibaktionen bleiben serverseitig geschützt,
- Gäste können offenen Gruppen anonym mit Ingame-Name, optionaler Flotte, Schiff, Rate und Notiz beitreten,
- Gruppenverwaltung ist serverseitig auf Gruppenleiter oder Admins beschränkt,
- Gruppen besitzen jetzt MVP-Felder für Fokus, Mindest-Schiffsrate, anonyme Teilnahme, Flottenhinweis, Ablauf nach 24 Stunden und Archivstatus,
- Admin-Endpunkte liegen unter dem eigenen OpenAPI-Tag `admin`,
- Schiffs-Builds speichern jetzt Ingame-Setup-Felder für Kanonen, Segel, Upgrades, Crew-Anzahl, Spezialcrew, Ladung, Munition, Verbrauchsgüter und Taktik,
- Build-Dropdowns kommen aus einem geseedeten Backend-Katalog `build_options` und können nach Schiff gefiltert werden,
- `wosb-dev`, `wosb-seed` und `wosb-clean-pycache` bleiben als Konsolenkommandos erhalten.

## Starten

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e .
wosb-dev
```

API-Dokumentation: <http://localhost:8000/docs>

## Datenbank seeden

```bash
wosb-seed --reset
```

Demo-Logins:

```text
Admin:  demo / demo123
Member: captain / captain123
```

## Python-Cache löschen

```bash
wosb-clean-pycache
wosb-clean-pycache --dry-run
wosb-clean-pycache --root ./src
```

## Relevante Endpunkte

Öffentlich:

- `GET /api/v1/health`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/ships`
- `GET /api/v1/ships/{ship_id}`
- `GET /api/v1/groups`
- `GET /api/v1/groups/{group_id}`
- `POST /api/v1/groups/{group_id}/join` – Gäste senden mindestens `display_name`; optional `fleet_name`, `custom_ship_name`, `custom_ship_rate`, `note`
- `POST /api/v1/groups/{group_id}/close` – Gruppenleiter/Admin archiviert eine Gruppe
- `DELETE /api/v1/groups/participations/{join_token}`
- `GET /api/v1/builds`
- `GET /api/v1/builds/options/catalog` – geseedete Optionen für Build-Designer; optional `category` und `ship_id`
- `GET /api/v1/builds/{build_id}`

Authentifiziert:

- `GET /api/v1/auth/me`
- `GET /api/v1/groups/manageable`
- `POST /api/v1/groups`
- `PUT /api/v1/groups/{group_id}`
- `DELETE /api/v1/groups/{group_id}` – nur für Entwickler-/Admin-Cleanup; UI nutzt reguläres Schließen
- `GET /api/v1/profile/me`
- `PUT /api/v1/profile/me`
- `POST /api/v1/builds`

Admin:

- `GET /api/v1/admin/groups`

## Hinweis zur Authentifizierung

Das Backend entscheidet über Freischaltung, Rollen und Gruppenrechte. Das Frontend nutzt diese Informationen nur zur Anzeige. Kritische Aktionen wie Gruppen bearbeiten/löschen werden im Backend erneut geprüft.

Für Produktion sollte später ein etablierter Auth-Flow mit Refresh-Tokens, Passwort-Reset, E-Mail-Verifikation und Alembic-Migrationen ergänzt werden.

## Hinweise zum aktuellen Stand

- Builds enthalten nun optional `build_role`, `crew_target`, `cannon_setup`, `sail_setup` und `special_crew_setup`.
- Das Frontend nutzt Overlays und Dropdowns für Gruppen- und Build-Erstellung; Backend-Rechte bleiben serverseitig geschützt.


## Build-Designer-Katalog

`wosb-seed --reset` legt neben den Schiffen auch einen Build-Optionen-Katalog an. Darin enthalten sind u. a.:

- Segel-Slot-Optionen,
- normale Upgrade-Slots und Spezialslot-Hinweise,
- Waffen-/Kanonen-Kategorien,
- Munition und taktische Payloads,
- Verbrauchsgüter,
- Crew-Fokus und Spezialcrew-Bausteine,
- Ladungs-/Hold-Bausteine.

Die Optionen sind bewusst editierbare UX-Bausteine. Einige Items sind öffentlich dokumentiert, andere sind community-/meta-inspiriert und im Seed mit Quellenhinweis markiert.
