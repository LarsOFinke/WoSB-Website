from __future__ import annotations

EVENT_CATALOG = (
    ("integration.test", "integration", "Manual connectivity and payload test."),
    ("registration.request.created", "registrations", "A new access request was submitted."),
    ("registration.request.approved", "registrations", "An access request was approved."),
    ("registration.request.rejected", "registrations", "An access request was rejected."),
    ("squad.created", "squads", "A squad was created."),
    ("squad.updated", "squads", "A squad was updated."),
    ("squad.archived", "squads", "A squad was archived."),
    ("squad.member.added", "squads", "A member was added to a squad."),
    ("squad.member.updated", "squads", "A squad membership was updated."),
    ("squad.member.removed", "squads", "A member was removed from a squad."),
    ("calendar.event.created", "calendar", "A fleet or squad event was created."),
    ("calendar.event.updated", "calendar", "A fleet or squad event was updated."),
    ("calendar.event.cancelled", "calendar", "A fleet or squad event was cancelled."),
    ("guide.created", "content", "A new guide was published."),
    ("guide.updated", "content", "A published guide was updated."),
    ("guide.removed", "content", "A guide was removed from publication."),
    ("newcomer_guide.updated", "content", "The starter guide was updated."),
    ("build.created", "builds", "A new build was created."),
    ("build.updated", "builds", "A build was updated."),
    ("build.removed", "builds", "A build was removed."),
    ("forum.thread.created", "forum", "A new forum thread was created."),
    ("forum.thread.updated", "forum", "A forum thread was updated."),
)
EVENT_TYPES = {row[0] for row in EVENT_CATALOG}

DEFAULT_MESSAGES = {
    "integration.test": "RBF-Verbindungstest für **{destination.name}**.",
    "registration.request.created": "Neue Registrierung: **{data.display_name}** (`{data.username}`).",
    "registration.request.approved": "Registrierung freigegeben: **{data.display_name}** (`{data.username}`).",
    "registration.request.rejected": "Registrierung abgelehnt: **{data.display_name}** (`{data.username}`).",
    "squad.created": "Neues Squad: **{data.name}**.",
    "squad.updated": "Squad aktualisiert: **{data.name}**.",
    "squad.archived": "Squad archiviert: **{data.name}**.",
    "squad.member.added": "**{data.member_display_name}** wurde dem Squad **{data.squad_name}** hinzugefügt.",
    "squad.member.updated": "Mitgliedschaft in **{data.squad_name}** wurde aktualisiert.",
    "squad.member.removed": "Ein Mitglied wurde aus **{data.squad_name}** entfernt.",
    "calendar.event.created": "Neuer Termin: **{data.title}**.",
    "calendar.event.updated": "Termin aktualisiert: **{data.title}**.",
    "calendar.event.cancelled": "Termin abgesagt: **{data.title}**.",
    "guide.created": "Neuer Guide: **{data.title}**.",
    "guide.updated": "Guide aktualisiert: **{data.title}**.",
    "guide.removed": "Guide entfernt: **{resource.id}**.",
    "newcomer_guide.updated": "Der Einsteiger-Guide wurde aktualisiert.",
    "build.created": "Neuer Build: **{data.name}**.",
    "build.updated": "Build aktualisiert: **{data.name}**.",
    "build.removed": "Build entfernt: **{resource.id}**.",
    "forum.thread.created": "Neuer Forenbeitrag: **{data.title}**.",
    "forum.thread.updated": "Forenbeitrag aktualisiert: **{data.title}**.",
}

__all__ = ["DEFAULT_MESSAGES", "EVENT_CATALOG", "EVENT_TYPES"]
