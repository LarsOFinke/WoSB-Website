# Single Fleet Refactor

## Ziel

Die Flottenlogik wurde von mehreren geplanten Flotten auf genau eine offizielle Flotte, die **Royal Blackwater Fleet**, umgestellt. Dadurch wird die Produktlogik einfacher: Nutzer bewerben sich nicht mehr bei einer von zehn Flotten, sondern für eine zentrale Flotte. Aufgaben wie Handel, Port-Battles, Training oder Logistik werden innerhalb dieser Flotte über Einteilungen, Rollen, Kalender und Gruppensuche organisiert.

## Datenmodell

Die Tabelle `fleets` bleibt erhalten, enthält im frischen Seed aber nur noch den Singleton `royal-blackwater-fleet`. Dadurch bleiben bestehende APIs und spätere Erweiterbarkeit erhalten, ohne im UI mehrere Flotten vorzutäuschen.

`fleet_memberships` ist die zentrale Quelle für offizielle Flottenzugehörigkeit. Pro Nutzer ist nur eine Membership vorgesehen. Das Profil verweist weiterhin über `user_profiles.primary_fleet_membership_id` auf diese Membership, sodass Status, Rolle, Flottenname und Verzeichnisdaten nicht kopiert werden.

Erweiterte Verzeichnisfelder auf `fleet_memberships`:

- `assignment`
- `availability`
- `preferred_ships`
- `timezone`
- `discord_handle`
- `admin_note`

## Registrierung

Die Registrierung erzeugt weiterhin zuerst eine Admin-Freigabe in `registration_requests`. Nutzer können dabei optional die Bewerbung zur offiziellen Flotte aktivieren. Nach Admin-Freigabe wird daraus automatisch:

1. ein aktiver User,
2. ein UserProfile,
3. bei aktivierter Flottenbewerbung eine pending `fleet_membership`,
4. die zentrale Profil-Verknüpfung auf diese Membership.

## Verwaltung

`/fleets` ist jetzt die Flottenverwaltung für die zentrale Flotte. `/fleets/manage` bleibt als Redirect aus älteren Builds erhalten. Die Ansicht enthält:

- Flottenprofil / Leitlinien,
- Bewerbungen,
- Mitgliederverwaltung,
- erweitertes Mitgliederverzeichnis.

Admins können die Flotte immer verwalten. Flottenadmiräle und Flottenlieutenants können sie verwalten, wenn ihre Membership aktiv ist.

## Lokaler Reset

Für ein sauberes Schema nach diesem Refactor:

```bash
cd backend
rbf-seed --reset
```
