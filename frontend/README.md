# WoSB Frontend

Vue 3 + Vite Frontend für die WoSB Gruppenmanagement-Blaupause.

## Start

```bash
npm install
npm run dev
```

Das Frontend erwartet das Backend unter `http://127.0.0.1:8000`. Der Vite-Proxy leitet `/api/*` entsprechend weiter.

## Rechtefluss

- Public: Home, Login, Registrierung, Gruppenliste, Buildliste.
- Gäste: Gruppen und Builds einsehen; offenen Gruppen mit Anzeigenamen beitreten.
- Geschützt: Gruppenverwaltung, Profil, neue Gruppen erstellen, neue Builds erstellen.
- Admin: Admin-Panel.

Die Routen und Buttons werden im Frontend nur komfortabel ein- oder ausgeblendet. Die eigentliche Freischaltung geschieht über das Backend via `GET /api/v1/auth/me`, Rollen im signierten Bearer-Token und serverseitige Owner/Admin-Prüfungen.

Demo-Logins nach `wosb-seed --reset`:

```text
Admin:  demo / demo123
Member: captain / captain123
```


## Builds

Der Reiter Builds ist auf WoSB-Schiffs-Builds ausgelegt. Ein Build kann ein konkretes Schiff aus dem Backend-Katalog referenzieren und Ingame-Setup-Felder wie Kanonen/Waffen, Segel-Slot, Upgrade-Slots, Crew-Anzahl, Spezialcrew, Ladung, Munition, Verbrauchsgüter, Taktik und Notizen speichern. Die Dropdowns kommen aus dem geseedeten Backend-Katalog `/api/v1/builds/options/catalog` und werden passend zum gewählten Schiff gefiltert.


## Gruppen

Die Gruppenliste ist öffentlich. Karten und Details zeigen Fokus, Status, Leitung, Mindest-Schiffsrate, bevorzugtes Schiff, Flottenhinweis, Ablaufzeit, freie Plätze und Teilnehmer. Gäste können offenen Gruppen beitreten, wenn anonyme Teilnahme erlaubt ist; Erstellen und Verwaltung bleiben geschützt.
