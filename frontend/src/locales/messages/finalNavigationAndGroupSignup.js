export const finalNavigationAndGroupSignupMessages = {
  en: {
    common: {
      home: 'Fleet portal',
      groups: 'Group search',
      myGroupSearches: 'My group searches',
    },
    fleets: {
      application: {
        applyWithoutLogin: 'Apply to the fleet',
      },
    },
    groups: {
      fields: {
        startTime: 'Start time',
        endTime: 'End time',
        schedule: 'Schedule',
        linkedBuild: 'Linked build',
      },
      list: {
        title: 'Group search',
        subtitle: 'Find scheduled fleet runs, sign up with a ship or link one of your saved builds.',
        newGroup: 'New group search',
        loginToCreate: 'Login to create',
        announcementMode: 'Signup enabled',
      },
      create: {
        title: 'New group search',
        subtitle: 'Create a scheduled group call with optional signup requirements.',
        timeRangeInvalid: 'End time must be after start time.',
        sections: {
          schedule: 'Schedule',
          scheduleText: 'Add an optional time window so members know when the run starts and ends.',
          requirementsText: 'Set seats, guest access and an optional allowed ship-rate span.',
        },
      },
      detail: {
        announcementEyebrow: 'Group search',
        overviewTitle: 'Signup overview',
        noSchedule: 'No fixed time',
        displayNamePlaceholder: 'Captain name',
        noLinkedBuild: 'No linked build',
        joinNotePlaceholder: 'Optional note for the group lead ...',
        joinClosedTitle: 'Signup is closed',
        joinClosedText: 'This group is full, closed or expired.',
      },
    },
    myGroups: {
      title: 'My group searches',
      subtitle: 'Manage group searches you created yourself.',
      create: 'Create group search',
      manageTitle: 'Your group searches',
      manageText: 'Search your group searches and close calls that are no longer active.',
      searchPlaceholder: 'Search your group searches ...',
      loading: 'Loading your group searches ...',
      loadError: 'Your group searches could not be loaded.',
      emptyText: 'You have not created a group search yet.',
      profileCardTitle: 'My group searches',
      profileCardText: 'Manage your scheduled group searches, signups and closed calls.',
    },
    logs: {
      dbOnly: 'Logs are stored in the database and shown here; backend console logging is disabled by default.',
      clientIp: 'Client IP',
      userAgent: 'User agent',
      queryString: 'Query',
    },
  },
  de: {
    common: {
      home: 'Flottenportal',
      groups: 'Gruppensuche',
      myGroupSearches: 'Meine Gruppensuchen',
    },
    fleets: {
      application: {
        applyWithoutLogin: 'Bei der Flotte bewerben',
      },
    },
    groups: {
      fields: {
        startTime: 'Startzeit',
        endTime: 'Endzeit',
        schedule: 'Zeitraum',
        linkedBuild: 'Verknüpfter Build',
      },
      list: {
        title: 'Gruppensuche',
        subtitle: 'Finde geplante Flottenrunden, melde dich mit Schiff an oder verknüpfe einen gespeicherten Build.',
        newGroup: 'Neue Gruppensuche',
        loginToCreate: 'Einloggen zum Erstellen',
        announcementMode: 'Anmeldung aktiv',
      },
      create: {
        title: 'Neue Gruppensuche',
        subtitle: 'Erstelle einen geplanten Gruppenaufruf mit optionalen Anforderungen für Anmeldungen.',
        timeRangeInvalid: 'Die Endzeit muss nach der Startzeit liegen.',
        sections: {
          schedule: 'Zeitraum',
          scheduleText: 'Ergänze optional ein Zeitfenster, damit Mitglieder wissen, wann die Runde startet und endet.',
          requirementsText: 'Setze Plätze, Gastzugriff und optional eine erlaubte Schiffsraten-Spanne.',
        },
      },
      detail: {
        announcementEyebrow: 'Gruppensuche',
        overviewTitle: 'Anmeldeübersicht',
        noSchedule: 'Kein fester Zeitraum',
        displayNamePlaceholder: 'Kapitänsname',
        noLinkedBuild: 'Kein verknüpfter Build',
        joinNotePlaceholder: 'Optionale Notiz für die Gruppenleitung ...',
        joinClosedTitle: 'Anmeldung geschlossen',
        joinClosedText: 'Diese Gruppe ist voll, geschlossen oder abgelaufen.',
      },
    },
    myGroups: {
      title: 'Meine Gruppensuchen',
      subtitle: 'Verwalte Gruppensuchen, die du selbst erstellt hast.',
      create: 'Gruppensuche erstellen',
      manageTitle: 'Deine Gruppensuchen',
      manageText: 'Durchsuche deine Gruppensuchen und schließe Aufrufe, die nicht mehr aktiv sind.',
      searchPlaceholder: 'Deine Gruppensuchen durchsuchen ...',
      loading: 'Deine Gruppensuchen werden geladen ...',
      loadError: 'Deine Gruppensuchen konnten nicht geladen werden.',
      emptyText: 'Du hast noch keine Gruppensuche erstellt.',
      profileCardTitle: 'Meine Gruppensuchen',
      profileCardText: 'Verwalte deine geplanten Gruppensuchen, Anmeldungen und geschlossenen Aufrufe.',
    },
    logs: {
      dbOnly: 'Logs werden in der Datenbank gespeichert und hier angezeigt; Backend-Konsolenlogging ist standardmäßig deaktiviert.',
      clientIp: 'Client-IP',
      userAgent: 'User-Agent',
      queryString: 'Query',
    },
  },
}
