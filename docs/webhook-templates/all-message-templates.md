# RBF Webhook-Nachrichten-Templates

Diese Datei enthält alle aktuell unterstützten Vorlagen in einem Dokument. Für direktes Kopieren ohne Überschriften stehen dieselben Inhalte zusätzlich einzeln unter `message-templates/`.

## `integration.test`

```text
🧪 **RBF-Webhook-Test**
Ziel: **{destination.name}**
Nachricht: {data.message}
Event: `{event}`
```

## `registration.request.created`

```text
🆕 **Neue Registrierungsanfrage**
Name: **{data.display_name}**
Benutzername: `{data.username}`
Flottenbewerbung: `{data.wants_fleet_membership}`
Flotten-ID: `{data.fleet_id}`
```

## `registration.request.approved`

```text
✅ **Registrierung freigegeben**
Name: **{data.display_name}**
Benutzername: `{data.username}`
Freigegeben von: **{actor.display_name}**
Entscheidungsnotiz: {data.decision_note}
```

## `registration.request.rejected`

```text
⛔ **Registrierung abgelehnt**
Name: **{data.display_name}**
Benutzername: `{data.username}`
Abgelehnt von: **{actor.display_name}**
Entscheidungsnotiz: {data.decision_note}
```

## `squad.created`

```text
🛡️ **Neues Squad erstellt**
Name: **{data.name}**
Slug: `{data.slug}`
Mitglieder: `{data.member_count}`
Erstellt von: **{actor.display_name}**
```

## `squad.updated`

```text
🛠️ **Squad aktualisiert**
Name: **{data.name}**
Mitglieder: `{data.member_count}`
Geändert von: **{actor.display_name}**
```

## `squad.archived`

```text
📦 **Squad archiviert**
Name: **{data.name}**
Letzter Mitgliederstand: `{data.member_count}`
Archiviert von: **{actor.display_name}**
```

## `squad.member.added`

```text
➕ **Squad-Mitglied hinzugefügt**
Squad: **{data.squad_name}**
Mitglied: **{data.member_display_name}**
Rolle: `{data.member_role}`
Ausgeführt von: **{actor.display_name}**
```

## `squad.member.updated`

```text
🔄 **Squad-Mitgliedschaft aktualisiert**
Squad: **{data.squad_name}**
Mitgliedschafts-ID: `{data.member_id}`
Ausgeführt von: **{actor.display_name}**
```

## `squad.member.removed`

```text
➖ **Squad-Mitglied entfernt**
Squad: **{data.squad_name}**
Mitgliedschafts-ID: `{data.member_id}`
Ausgeführt von: **{actor.display_name}**
```

## `calendar.event.created`

```text
📅 **Neuer Termin**
Titel: **{data.title}**
Kategorie: `{data.category}`
Beginn: `{data.start_at}`
Ende: `{data.end_at}`
Ort: {data.location}
Erstellt von: **{actor.display_name}**
```

## `calendar.event.updated`

```text
🗓️ **Termin aktualisiert**
Titel: **{data.title}**
Kategorie: `{data.category}`
Beginn: `{data.start_at}`
Ende: `{data.end_at}`
Ort: {data.location}
Geändert von: **{actor.display_name}**
```

## `calendar.event.cancelled`

```text
❌ **Termin abgesagt**
Titel: **{data.title}**
Beginn: `{data.start_at}`
Abgesagt von: **{actor.display_name}**
```

## `guide.created`

```text
📘 **Neuer Guide veröffentlicht**
Titel: **{data.title}**
Kategorie: `{data.category}`
Autor: **{data.owner.display_name}**
Zusammenfassung: {data.summary}
```

## `guide.updated`

```text
📝 **Guide aktualisiert**
Titel: **{data.title}**
Kategorie: `{data.category}`
Geändert von: **{actor.display_name}**
Zusammenfassung: {data.summary}
```

## `guide.removed`

```text
🗑️ **Guide entfernt**
Titel: **{data.title}**
Guide-ID: `{data.id}`
Entfernt von: **{actor.display_name}**
```

## `newcomer_guide.updated`

```text
🧭 **Einsteiger-Guide aktualisiert**
Titel: **{data.title}**
Aktualisiert von: **{actor.display_name}**
```

## `build.created`

```text
⚓ **Neuer Build erstellt**
Build: **{data.build_name}**
Schiff: **{data.ship.name}**
Typ: `{data.build_type}`
Erstellt von: **{actor.display_name}**
```

## `build.updated`

```text
🔧 **Build aktualisiert**
Build: **{data.build_name}**
Schiff: **{data.ship.name}**
Typ: `{data.build_type}`
Geändert von: **{actor.display_name}**
```

## `build.removed`

```text
🗑️ **Build entfernt**
Build: **{data.build_name}**
Build-ID: `{data.id}`
Entfernt von: **{actor.display_name}**
```

## `forum.thread.created`

```text
💬 **Neuer Forenbeitrag**
Titel: **{data.title}**
Kategorie: `{data.category}`
Autor: **{data.owner.display_name}**
```

## `forum.thread.updated`

```text
✏️ **Forenbeitrag aktualisiert**
Titel: **{data.title}**
Kategorie: `{data.category}`
Geändert von: **{actor.display_name}**
Antworten: `{data.reply_count}`
```
