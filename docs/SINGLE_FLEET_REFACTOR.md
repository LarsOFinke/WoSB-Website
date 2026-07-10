# Single Fleet Refactor

## Ziel

Die Anwendung verwaltet genau eine offizielle Flotte, die **Royal Blackwater Fleet**. Aktivitäten werden innerhalb dieser Flotte über Rollen, Squads, Kalender und Gruppensuche organisiert.

## Datenmodell

`fleet_memberships` ist die zentrale Quelle für die offizielle Flottenzugehörigkeit. Pro Nutzer ist eine Membership vorgesehen. Das Profil speichert keinen zusätzlichen Membership-Zeiger; Status, Flottenname und Rolle werden aus der Membership abgeleitet.

Flottenrollen stehen normalisiert in `fleet_roles`. `fleet_memberships.fleet_role_id` verweist darauf. Bevorzugte Schiffe werden als einzelne Zeilen in `fleet_membership_ship_preferences` gespeichert.

## Registrierung und Bewerbung

Die Registrierung erzeugt ausschließlich einen prüfbaren Portal-Account-Antrag. Nach Admin-Freigabe und Login kann der Nutzer separat eine Flottenbewerbung absenden. Dadurch werden Accountfreigabe und Flottenaufnahme nicht vermischt.

## Verwaltung und Leitung

Administratoren, Moderatoren sowie aktive Fleet Admirals und Fleet Lieutenants können die Flotte verwalten. Die aktive Leitung wird aus den normalisierten Membership-Rollen abgeleitet und auf Landing-Page, öffentlicher Flottenseite und im Fleet Management einheitlich angezeigt.

Squads referenzieren aktive Fleet Memberships und vergeben nur squadbezogene Rollen; sie verändern keine globale Flotten- oder Site-Rolle.
