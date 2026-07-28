export const outboundWebhookManagementMessages = {
  "en": {
    "admin": {
      "tabs": {
        "integrations": "Discord webhooks"
      },
      "audit": {
        "entities": {
          "outbound_webhook": "Discord webhook"
        }
      },
      "webhooks": {
        "eyebrow": "Channel automation",
        "title": "Discord channel webhooks",
        "subtitle": "Send selected website events directly to Discord channels.",
        "loading": "Loading Discord webhooks ...",
        "empty": "No Discord webhooks configured yet.",
        "confirmDelete": "Delete webhook “{name}” and its delivery history?",
        "summary": {
          "total": "Configured",
          "totalHint": "All Discord destinations",
          "active": "Active",
          "activeHint": "Receive new events",
          "failing": "Needs attention",
          "failingHint": "Most recent delivery failed",
          "deliveries": "Success / failed",
          "deliveriesHint": "Stored delivery history"
        },
        "editor": {
          "eyebrow": "Channel destination",
          "createTitle": "Create Discord webhook",
          "editTitle": "Edit Discord webhook"
        },
        "fields": {
          "name": "Name",
          "endpoint": "Discord webhook URL",
          "active": "Webhook active",
          "scope": "Scope",
          "scopeId": "Scope ID",
          "discordUsername": "Discord sender name",
          "discordAvatar": "Discord avatar URL",
          "template": "Message template",
          "events": "Subscribed events",
          "broadcastEnabled": "Available for manual broadcasts"
        },
        "placeholders": {
          "name": "RBF · Build notifications",
          "keepEndpoint": "Leave blank to keep the current secret Discord URL",
          "template": "Paste a template from docs/webhook-templates/message-templates/"
        },
        "endpointHint": "The Discord URL is treated like a password and is masked after saving.",
        "templateHint": "Discord supports Markdown. The available placeholders depend on the selected event.",
        "eventsHint": "Choose the events posted to this channel. The same event can be assigned to any number of webhooks and channels.",
        "templatePicker": {
          "label": "Autofill from event template",
          "placeholder": "Choose a repository template ...",
          "apply": "Autofill message",
          "useDefaults": "Use event defaults",
          "hint": "Choose an event to load its versioned English template. A custom message is shared by every subscribed event; leave it blank to use each event-specific default."
        },
        "eventPicker": {
          "none": "No events selected",
          "selected": "{count} event(s) selected",
          "summaryHint": "Open to manage subscriptions",
          "search": "Search events ...",
          "selectVisible": "Select visible",
          "clear": "Clear",
          "empty": "No matching events.",
          "remove": "Remove {event}"
        },
        "actions": {
          "create": "Create webhook",
          "edit": "Edit",
          "test": "Send test",
          "retry": "Retry"
        },
        "status": {
          "active": "Active",
          "inactive": "Inactive",
          "success": "Delivered",
          "failed": "Failed",
          "queued": "Queued",
          "processing": "Delivering"
        },
        "scopes": {
          "global": "Global",
          "fleet": "Fleet",
          "squad": "Squad"
        },
        "readOnly": {
          "eyebrow": "Read-only access",
          "title": "Delivery monitor",
          "hint": "Only administrators can change Discord webhook destinations."
        },
        "list": {
          "eyebrow": "Configured channels",
          "title": "Discord webhook subscriptions",
          "events": "events",
          "lastSuccess": "Last success",
          "lastFailure": "Last failure",
          "broadcastTarget": "Broadcast target"
        },
        "deliveries": {
          "eyebrow": "Delivery monitor",
          "title": "Recent Discord deliveries",
          "allWebhooks": "All webhooks",
          "allStatuses": "All statuses",
          "empty": "No deliveries recorded yet.",
          "created": "Created",
          "webhook": "Discord destination",
          "event": "Event",
          "status": "Status",
          "details": "Details",
          "open": "Open",
          "collapsedHint": "Collapsed by default so tests and refreshes do not move the page.",
          "manageHint": "Filter, retry or permanently remove stored delivery records.",
          "clear": "Delete history",
          "clearNow": "Delete history now",
          "deleting": "Deleting ...",
          "clearConfirmTitle": "Delete this delivery history?",
          "clearFilteredHint": "Only records matching the current webhook, status and event filters are removed.",
          "clearAllHint": "All stored delivery records are removed. Webhook configurations remain unchanged.",
          "clearSuccess": "{count} delivery record(s) deleted.",
          "deleteConfirm": "Delete this delivery record?",
          "deleteSuccess": "Delivery record deleted.",
          "deleteError": "Delivery history could not be deleted."
        },
        "messages": {
          "created": "Discord webhook created.",
          "updated": "Discord webhook updated.",
          "testSuccess": "Test delivery succeeded.",
          "testFailed": "Test delivery failed. Review the history.",
          "deleted": "Discord webhook deleted.",
          "retrySuccess": "Retry succeeded.",
          "retryFailed": "Retry failed."
        },
        "validation": { "title": "Check the webhook details.", "name": "Enter a name with at least 3 characters.", "endpointRequired": "Paste the Discord webhook URL.", "endpointInvalid": "Use the complete Discord channel webhook URL, including its ID and token.", "scope": "Enter a valid fleet or squad ID.", "events": "Select at least one event or enable manual broadcasts." },
        "errors": {
          "load": "Discord webhooks could not be loaded.",
          "save": "Discord webhook could not be saved.",
          "test": "Test delivery could not be sent.",
          "delete": "Discord webhook could not be deleted.",
          "retry": "Delivery could not be retried."
        },
        "broadcast": {
          "pageEyebrow": "External fleet communication",
          "pageTitle": "Discord broadcasts",
          "pageSubtitle": "Manage external Discord destinations separately from website automation and coordinate directly with partner fleets and other servers.",
          "openPanel": "Open broadcast panel",
          "openAutomation": "Website webhooks",
          "historyTitle": "Broadcast delivery history",
          "managementEyebrow": "External destinations",
          "managementTitle": "Broadcast webhook administration",
          "managementSubtitle": "These Discord endpoints are maintained for diplomacy, fleet coordination and cross-server agreements, independently from website events.",
          "eyebrow": "Manual channel message",
          "title": "Broadcast panel",
          "subtitle": "Write one message and send it directly to several configured Discord channels at once.",
          "targets": {
            "eyebrow": "Destinations",
            "title": "Broadcast channels",
            "selectAll": "Select all",
            "clearAll": "Clear selection",
            "create": "Add broadcast destination",
            "createTitle": "Create broadcast destination",
            "editTitle": "Edit broadcast destination",
            "namePlaceholder": "Partner fleet · Diplomacy channel",
            "empty": "No active broadcast targets are configured.",
            "emptyManaged": "No external broadcast destinations have been configured yet.",
            "externalHint": "External Discord server or partner-fleet communication channel",
            "sharedAutomation": "Also used by {count} website event(s)",
            "separationHint": "New destinations created here are broadcast-only and do not receive automatic website events.",
            "created": "Broadcast destination created.",
            "updated": "Broadcast destination updated.",
            "deleted": "Broadcast destination deleted.",
            "detached": "Broadcast access removed; the website-event subscription remains active.",
            "confirmDelete": "Delete broadcast destination “{name}” and its delivery history?",
            "confirmDetach": "Remove “{name}” from broadcasts? Its {count} website-event subscription(s) remain configured.",
            "loadError": "Broadcast destinations could not be loaded.",
            "saveError": "Broadcast destination could not be saved.",
            "deleteError": "Broadcast destination could not be deleted."
          },
          "message": {
            "eyebrow": "Compose",
            "title": "Discord message"
          },
          "fields": {
            "message": "Message"
          },
          "placeholders": {
            "message": "Write a Discord Markdown message ..."
          },
          "messageHint": "Discord Markdown is supported. Automatic mentions are disabled for safety.",
          "selected": "{count} channel(s) selected",
          "actions": {
            "send": "Send broadcast",
            "sending": "Sending ..."
          },
          "messages": {
            "queued": "Broadcast queued for {count} channel(s)."
          },
          "errors": {
            "load": "Broadcast targets could not be loaded.",
            "send": "The broadcast could not be sent."
          }
        }
      }
    }
  },
  "de": {
    "admin": {
      "tabs": {
        "integrations": "Discord-Webhooks"
      },
      "audit": {
        "entities": {
          "outbound_webhook": "Discord-Webhook"
        }
      },
      "webhooks": {
        "eyebrow": "Channel-Automatisierung",
        "title": "Discord-Channel-Webhooks",
        "subtitle": "Ausgewählte Website-Events direkt an Discord-Channels senden.",
        "loading": "Discord-Webhooks werden geladen ...",
        "empty": "Noch keine Discord-Webhooks konfiguriert.",
        "confirmDelete": "Webhook „{name}“ samt Zustellhistorie löschen?",
        "summary": {
          "total": "Konfiguriert",
          "totalHint": "Alle Discord-Ziele",
          "active": "Aktiv",
          "activeHint": "Empfangen neue Events",
          "failing": "Prüfung nötig",
          "failingHint": "Letzte Zustellung fehlgeschlagen",
          "deliveries": "Erfolg / Fehler",
          "deliveriesHint": "Gespeicherte Zustellhistorie"
        },
        "editor": {
          "eyebrow": "Channel-Ziel",
          "createTitle": "Discord-Webhook erstellen",
          "editTitle": "Discord-Webhook bearbeiten"
        },
        "fields": {
          "name": "Bezeichnung",
          "endpoint": "Discord-Webhook-URL",
          "active": "Webhook aktiv",
          "scope": "Gültigkeitsbereich",
          "scopeId": "Bereichs-ID",
          "discordUsername": "Discord-Absendername",
          "discordAvatar": "Discord-Avatar-URL",
          "template": "Nachrichten-Template",
          "events": "Abonnierte Events",
          "broadcastEnabled": "Für manuelle Broadcasts verfügbar"
        },
        "placeholders": {
          "name": "RBF · Build-Benachrichtigungen",
          "keepEndpoint": "Leer lassen, um die aktuelle geheime Discord-URL beizubehalten",
          "template": "Vorlage aus docs/webhook-templates/message-templates/ einfügen"
        },
        "endpointHint": "Die Discord-URL wird wie ein Passwort behandelt und nach dem Speichern maskiert.",
        "templateHint": "Discord unterstützt Markdown. Die verfügbaren Platzhalter hängen vom gewählten Event ab.",
        "eventsHint": "Wähle die Events für diesen Channel. Dasselbe Event kann beliebig vielen Webhooks und Channels zugeordnet werden.",
        "templatePicker": {
          "label": "Aus Event-Template vorausfüllen",
          "placeholder": "Repository-Template auswählen ...",
          "apply": "Nachricht vorausfüllen",
          "useDefaults": "Event-Standards verwenden",
          "hint": "Wähle ein Event, um dessen versioniertes englisches Template zu laden. Eine eigene Nachricht gilt für alle abonnierten Events; leer lassen nutzt den jeweiligen Event-Standard."
        },
        "eventPicker": {
          "none": "Keine Events ausgewählt",
          "selected": "{count} Event(s) ausgewählt",
          "summaryHint": "Öffnen, um Abonnements zu verwalten",
          "search": "Events durchsuchen ...",
          "selectVisible": "Sichtbare auswählen",
          "clear": "Leeren",
          "empty": "Keine passenden Events.",
          "remove": "{event} entfernen"
        },
        "actions": {
          "create": "Webhook erstellen",
          "edit": "Bearbeiten",
          "test": "Test senden",
          "retry": "Wiederholen"
        },
        "status": {
          "active": "Aktiv",
          "inactive": "Inaktiv",
          "success": "Zugestellt",
          "failed": "Fehlgeschlagen",
          "queued": "Eingeplant",
          "processing": "Wird zugestellt"
        },
        "scopes": {
          "global": "Übergreifend",
          "fleet": "Flotte",
          "squad": "Einsatzgruppe"
        },
        "readOnly": {
          "eyebrow": "Nur Lesezugriff",
          "title": "Zustellmonitor",
          "hint": "Nur Administratoren können Discord-Webhook-Ziele ändern."
        },
        "list": {
          "eyebrow": "Konfigurierte Channels",
          "title": "Discord-Webhook-Abonnements",
          "events": "Events",
          "lastSuccess": "Letzter Erfolg",
          "lastFailure": "Letzter Fehler",
          "broadcastTarget": "Broadcast-Ziel"
        },
        "deliveries": {
          "eyebrow": "Zustellmonitor",
          "title": "Letzte Discord-Zustellungen",
          "allWebhooks": "Alle Webhooks",
          "allStatuses": "Alle Status",
          "empty": "Noch keine Zustellungen vorhanden.",
          "created": "Erstellt",
          "webhook": "Discord-Ziel",
          "event": "Event",
          "status": "Status",
          "details": "Details",
          "open": "Öffnen",
          "collapsedHint": "Standardmäßig eingeklappt, damit Tests und Aktualisierungen die Seite nicht verschieben.",
          "manageHint": "Gespeicherte Zustellungen filtern, wiederholen oder dauerhaft löschen.",
          "clear": "Historie löschen",
          "clearNow": "Historie jetzt löschen",
          "deleting": "Wird gelöscht ...",
          "clearConfirmTitle": "Diese Zustellhistorie löschen?",
          "clearFilteredHint": "Nur Einträge passend zu den aktuellen Webhook-, Status- und Event-Filtern werden entfernt.",
          "clearAllHint": "Alle gespeicherten Zustellungen werden entfernt. Die Webhook-Konfigurationen bleiben bestehen.",
          "clearSuccess": "{count} Zustell-Eintrag/Einträge gelöscht.",
          "deleteConfirm": "Diesen Zustell-Eintrag löschen?",
          "deleteSuccess": "Zustell-Eintrag gelöscht.",
          "deleteError": "Zustellhistorie konnte nicht gelöscht werden."
        },
        "messages": {
          "created": "Discord-Webhook erstellt.",
          "updated": "Discord-Webhook aktualisiert.",
          "testSuccess": "Testzustellung erfolgreich.",
          "testFailed": "Testzustellung fehlgeschlagen. Prüfe die Historie.",
          "deleted": "Discord-Webhook gelöscht.",
          "retrySuccess": "Wiederholung erfolgreich.",
          "retryFailed": "Wiederholung fehlgeschlagen."
        },
        "validation": { "title": "Prüfe die Webhook-Angaben.", "name": "Gib einen Namen mit mindestens 3 Zeichen ein.", "endpointRequired": "Füge die Discord-Webhook-URL ein.", "endpointInvalid": "Verwende die vollständige Discord-Channel-Webhook-URL inklusive ID und Token.", "scope": "Gib eine gültige Flotten- oder Squad-ID ein.", "events": "Wähle mindestens ein Event oder aktiviere manuelle Broadcasts." },
        "errors": {
          "load": "Discord-Webhooks konnten nicht geladen werden.",
          "save": "Discord-Webhook konnte nicht gespeichert werden.",
          "test": "Testzustellung konnte nicht gesendet werden.",
          "delete": "Discord-Webhook konnte nicht gelöscht werden.",
          "retry": "Zustellung konnte nicht wiederholt werden."
        },
        "broadcast": {
          "pageEyebrow": "Externe Flottenkommunikation",
          "pageTitle": "Discord-Broadcasts",
          "pageSubtitle": "Externe Discord-Ziele getrennt von der Website-Automatisierung verwalten und direkt mit Partnerflotten sowie anderen Servern kommunizieren.",
          "openPanel": "Broadcast-Panel öffnen",
          "openAutomation": "Website-Webhooks",
          "historyTitle": "Broadcast-Zustellhistorie",
          "managementEyebrow": "Externe Ziele",
          "managementTitle": "Broadcast-Webhook-Verwaltung",
          "managementSubtitle": "Diese Discord-Ziele dienen Diplomatie, Flottenabsprachen und serverübergreifender Kommunikation – unabhängig von automatischen Website-Events.",
          "eyebrow": "Manuelle Channel-Nachricht",
          "title": "Broadcast-Panel",
          "subtitle": "Eine Nachricht verfassen und gleichzeitig direkt an mehrere konfigurierte Discord-Channels senden.",
          "targets": {
            "eyebrow": "Ziele",
            "title": "Broadcast-Channels",
            "selectAll": "Alle auswählen",
            "clearAll": "Auswahl leeren",
            "create": "Broadcast-Ziel hinzufügen",
            "createTitle": "Broadcast-Ziel erstellen",
            "editTitle": "Broadcast-Ziel bearbeiten",
            "namePlaceholder": "Partnerflotte · Diplomatie-Channel",
            "empty": "Keine aktiven Broadcast-Ziele konfiguriert.",
            "emptyManaged": "Noch keine externen Broadcast-Ziele konfiguriert.",
            "externalHint": "Externer Discord-Server oder Kommunikationschannel einer Partnerflotte",
            "sharedAutomation": "Wird zusätzlich von {count} Website-Event(s) verwendet",
            "separationHint": "Neue Ziele aus diesem Bereich sind reine Broadcast-Ziele und erhalten keine automatischen Website-Events.",
            "created": "Broadcast-Ziel erstellt.",
            "updated": "Broadcast-Ziel aktualisiert.",
            "deleted": "Broadcast-Ziel gelöscht.",
            "detached": "Broadcast-Zugriff entfernt; das Website-Event-Abonnement bleibt bestehen.",
            "confirmDelete": "Broadcast-Ziel „{name}“ samt Zustellhistorie löschen?",
            "confirmDetach": "„{name}“ aus den Broadcasts entfernen? Die {count} Website-Event-Abonnements bleiben bestehen.",
            "loadError": "Broadcast-Ziele konnten nicht geladen werden.",
            "saveError": "Broadcast-Ziel konnte nicht gespeichert werden.",
            "deleteError": "Broadcast-Ziel konnte nicht gelöscht werden."
          },
          "message": {
            "eyebrow": "Verfassen",
            "title": "Discord-Nachricht"
          },
          "fields": {
            "message": "Nachricht"
          },
          "placeholders": {
            "message": "Discord-Markdown-Nachricht verfassen ..."
          },
          "messageHint": "Discord-Markdown wird unterstützt. Automatische Erwähnungen sind aus Sicherheitsgründen deaktiviert.",
          "selected": "{count} Channel(s) ausgewählt",
          "actions": {
            "send": "Broadcast senden",
            "sending": "Wird gesendet ..."
          },
          "messages": {
            "queued": "Broadcast für {count} Channel(s) eingeplant."
          },
          "errors": {
            "load": "Broadcast-Ziele konnten nicht geladen werden.",
            "send": "Der Broadcast konnte nicht gesendet werden."
          }
        }
      }
    }
  },
  "fr": {
    "admin": {
      "tabs": {
        "integrations": "Webhooks Discord"
      },
      "audit": {
        "entities": {
          "outbound_webhook": "Webhook Discord"
        }
      },
      "webhooks": {
        "eyebrow": "Automatisation des salons",
        "title": "Webhooks de salons Discord",
        "subtitle": "Envoyez les événements sélectionnés directement dans les salons Discord.",
        "loading": "Chargement des webhooks Discord ...",
        "empty": "Aucun webhook Discord configuré.",
        "confirmDelete": "Supprimer le webhook « {name} » et son historique ?",
        "summary": {
          "total": "Configurés",
          "totalHint": "Toutes les destinations Discord",
          "active": "Actifs",
          "activeHint": "Reçoivent les nouveaux événements",
          "failing": "À vérifier",
          "failingHint": "La dernière livraison a échoué",
          "deliveries": "Réussies / échouées",
          "deliveriesHint": "Historique enregistré"
        },
        "editor": {
          "eyebrow": "Destination du salon",
          "createTitle": "Créer un webhook Discord",
          "editTitle": "Modifier le webhook Discord"
        },
        "fields": {
          "name": "Nom",
          "endpoint": "URL du webhook Discord",
          "active": "Webhook actif",
          "scope": "Portée",
          "scopeId": "Identifiant de portée",
          "discordUsername": "Nom d’expéditeur Discord",
          "discordAvatar": "URL de l’avatar Discord",
          "template": "Modèle de message",
          "events": "Événements abonnés",
          "broadcastEnabled": "Disponible pour les diffusions manuelles"
        },
        "placeholders": {
          "name": "RBF · Notifications de builds",
          "keepEndpoint": "Laisser vide pour conserver l’URL Discord secrète actuelle",
          "template": "Coller un modèle depuis docs/webhook-templates/message-templates/"
        },
        "endpointHint": "L’URL Discord est traitée comme un mot de passe et masquée après enregistrement.",
        "templateHint": "Discord prend en charge Markdown. Les variables dépendent de l’événement choisi.",
        "eventsHint": "Choisissez les événements de ce salon. Un même événement peut être associé à plusieurs webhooks et salons.",
        "templatePicker": {
          "label": "Préremplir avec un modèle d’événement",
          "placeholder": "Choisir un modèle du dépôt ...",
          "apply": "Préremplir le message",
          "useDefaults": "Utiliser les modèles par défaut",
          "hint": "Choisissez un événement pour charger son modèle anglais versionné. Un message personnalisé s’applique à tous les événements abonnés ; laissez le champ vide pour utiliser le modèle propre à chaque événement."
        },
        "eventPicker": {
          "none": "Aucun événement sélectionné",
          "selected": "{count} événement(s) sélectionné(s)",
          "summaryHint": "Ouvrir pour gérer les abonnements",
          "search": "Rechercher des événements ...",
          "selectVisible": "Sélectionner les visibles",
          "clear": "Effacer",
          "empty": "Aucun événement correspondant.",
          "remove": "Retirer {event}"
        },
        "actions": {
          "create": "Créer le webhook",
          "edit": "Modifier",
          "test": "Envoyer un test",
          "retry": "Réessayer"
        },
        "status": {
          "active": "Actif",
          "inactive": "Inactif",
          "success": "Livré",
          "failed": "Échec",
          "queued": "En attente",
          "processing": "Livraison en cours"
        },
        "scopes": {
          "global": "Général",
          "fleet": "Flotte",
          "squad": "Escouade"
        },
        "readOnly": {
          "eyebrow": "Accès en lecture",
          "title": "Suivi des livraisons",
          "hint": "Seuls les administrateurs peuvent modifier les destinations Discord."
        },
        "list": {
          "eyebrow": "Salons configurés",
          "title": "Abonnements webhook Discord",
          "events": "événements",
          "lastSuccess": "Dernier succès",
          "lastFailure": "Dernier échec",
          "broadcastTarget": "Destination de diffusion"
        },
        "deliveries": {
          "eyebrow": "Suivi des livraisons",
          "title": "Livraisons Discord récentes",
          "allWebhooks": "Tous les webhooks",
          "allStatuses": "Tous les états",
          "empty": "Aucune livraison enregistrée.",
          "created": "Créé",
          "webhook": "Destination Discord",
          "event": "Événement",
          "status": "État",
          "details": "Détails"
        },
        "messages": {
          "created": "Webhook Discord créé.",
          "updated": "Webhook Discord mis à jour.",
          "testSuccess": "Livraison de test réussie.",
          "testFailed": "Échec du test. Consultez l’historique.",
          "deleted": "Webhook Discord supprimé.",
          "retrySuccess": "Nouvelle tentative réussie.",
          "retryFailed": "Nouvelle tentative échouée."
        },
        "validation": { "title": "Vérifiez les informations du webhook.", "name": "Saisissez un nom d’au moins 3 caractères.", "endpointRequired": "Collez l’URL du webhook Discord.", "endpointInvalid": "Utilisez l’URL complète du webhook de salon avec son ID et son jeton.", "scope": "Saisissez un ID de flotte ou d’escouade valide.", "events": "Sélectionnez un événement ou activez les diffusions manuelles." },
        "errors": {
          "load": "Impossible de charger les webhooks Discord.",
          "save": "Impossible d’enregistrer le webhook Discord.",
          "test": "Impossible d’envoyer le test.",
          "delete": "Impossible de supprimer le webhook Discord.",
          "retry": "Impossible de relancer la livraison."
        },
        "broadcast": {
          "openAutomation": "Webhooks du site",
          "eyebrow": "Message manuel",
          "title": "Panneau de diffusion",
          "subtitle": "Rédigez un message et envoyez-le directement à plusieurs salons Discord configurés.",
          "targets": {
            "eyebrow": "Destinations",
            "title": "Salons de diffusion",
            "selectAll": "Tout sélectionner",
            "clearAll": "Effacer la sélection",
            "empty": "Aucune destination active. Activez « Disponible pour les diffusions manuelles » sur au moins un webhook."
          },
          "message": {
            "eyebrow": "Rédaction",
            "title": "Message Discord"
          },
          "fields": {
            "message": "Contenu du message"
          },
          "placeholders": {
            "message": "Rédigez un message Discord en Markdown ..."
          },
          "messageHint": "Le Markdown Discord est pris en charge. Les mentions automatiques sont désactivées.",
          "selected": "{count} salon(s) sélectionné(s)",
          "actions": {
            "send": "Envoyer la diffusion",
            "sending": "Envoi ..."
          },
          "messages": {
            "queued": "Diffusion mise en file pour {count} salon(s)."
          },
          "errors": {
            "load": "Impossible de charger les destinations.",
            "send": "Impossible d’envoyer la diffusion."
          }
        }
      }
    }
  },
  "es": {
    "admin": {
      "tabs": {
        "integrations": "Webhooks de Discord"
      },
      "audit": {
        "entities": {
          "outbound_webhook": "Webhook de Discord"
        }
      },
      "webhooks": {
        "eyebrow": "Automatización de canales",
        "title": "Webhooks de canales de Discord",
        "subtitle": "Envía eventos seleccionados directamente a canales de Discord.",
        "loading": "Cargando webhooks de Discord ...",
        "empty": "Aún no hay webhooks de Discord.",
        "confirmDelete": "¿Eliminar el webhook «{name}» y su historial?",
        "summary": {
          "total": "Configurados",
          "totalHint": "Todos los destinos de Discord",
          "active": "Activos",
          "activeHint": "Reciben eventos nuevos",
          "failing": "Requieren atención",
          "failingHint": "La última entrega falló",
          "deliveries": "Correctas / fallidas",
          "deliveriesHint": "Historial guardado"
        },
        "editor": {
          "eyebrow": "Destino del canal",
          "createTitle": "Crear webhook de Discord",
          "editTitle": "Editar webhook de Discord"
        },
        "fields": {
          "name": "Nombre",
          "endpoint": "URL del webhook de Discord",
          "active": "Webhook activo",
          "scope": "Ámbito",
          "scopeId": "ID del ámbito",
          "discordUsername": "Nombre del remitente en Discord",
          "discordAvatar": "URL del avatar de Discord",
          "template": "Plantilla del mensaje",
          "events": "Eventos suscritos",
          "broadcastEnabled": "Disponible para difusiones manuales"
        },
        "placeholders": {
          "name": "RBF · Avisos de builds",
          "keepEndpoint": "Déjalo vacío para conservar la URL secreta actual",
          "template": "Pega una plantilla de docs/webhook-templates/message-templates/"
        },
        "endpointHint": "La URL de Discord se trata como una contraseña y se oculta después de guardar.",
        "templateHint": "Discord admite Markdown. Los marcadores dependen del evento elegido.",
        "eventsHint": "Selecciona los eventos de este canal. El mismo evento puede asignarse a varios webhooks y canales.",
        "templatePicker": {
          "label": "Autocompletar desde una plantilla de evento",
          "placeholder": "Elegir una plantilla del repositorio ...",
          "apply": "Autocompletar mensaje",
          "useDefaults": "Usar valores predeterminados",
          "hint": "Elige un evento para cargar su plantilla versionada en inglés. Un mensaje personalizado se aplica a todos los eventos suscritos; déjalo vacío para usar la plantilla propia de cada evento."
        },
        "eventPicker": {
          "none": "No hay eventos seleccionados",
          "selected": "{count} evento(s) seleccionado(s)",
          "summaryHint": "Abrir para gestionar suscripciones",
          "search": "Buscar eventos ...",
          "selectVisible": "Seleccionar visibles",
          "clear": "Limpiar",
          "empty": "No hay eventos coincidentes.",
          "remove": "Quitar {event}"
        },
        "actions": {
          "create": "Crear webhook",
          "edit": "Editar",
          "test": "Enviar prueba",
          "retry": "Reintentar"
        },
        "status": {
          "active": "Activo",
          "inactive": "Inactivo",
          "success": "Entregado",
          "failed": "Fallido",
          "queued": "En cola",
          "processing": "Entregando"
        },
        "scopes": {
          "global": "General",
          "fleet": "Flota",
          "squad": "Escuadrón"
        },
        "readOnly": {
          "eyebrow": "Acceso de lectura",
          "title": "Monitor de entregas",
          "hint": "Solo los administradores pueden cambiar los destinos de Discord."
        },
        "list": {
          "eyebrow": "Canales configurados",
          "title": "Suscripciones webhook de Discord",
          "events": "eventos",
          "lastSuccess": "Último éxito",
          "lastFailure": "Último fallo",
          "broadcastTarget": "Destino de difusión"
        },
        "deliveries": {
          "eyebrow": "Monitor de entregas",
          "title": "Entregas recientes a Discord",
          "allWebhooks": "Todos los webhooks",
          "allStatuses": "Todos los estados",
          "empty": "No hay entregas registradas.",
          "created": "Creado",
          "webhook": "Destino de Discord",
          "event": "Evento",
          "status": "Estado",
          "details": "Detalles"
        },
        "messages": {
          "created": "Webhook de Discord creado.",
          "updated": "Webhook de Discord actualizado.",
          "testSuccess": "Entrega de prueba correcta.",
          "testFailed": "La prueba falló. Revisa el historial.",
          "deleted": "Webhook de Discord eliminado.",
          "retrySuccess": "Reintento correcto.",
          "retryFailed": "El reintento falló."
        },
        "validation": { "title": "Revisa los datos del webhook.", "name": "Introduce un nombre de al menos 3 caracteres.", "endpointRequired": "Pega la URL del webhook de Discord.", "endpointInvalid": "Usa la URL completa del webhook del canal, con su ID y token.", "scope": "Introduce un ID de flota o escuadrón válido.", "events": "Selecciona un evento o activa las difusiones manuales." },
        "errors": {
          "load": "No se pudieron cargar los webhooks de Discord.",
          "save": "No se pudo guardar el webhook de Discord.",
          "test": "No se pudo enviar la prueba.",
          "delete": "No se pudo eliminar el webhook de Discord.",
          "retry": "No se pudo reintentar la entrega."
        },
        "broadcast": {
          "openAutomation": "Webhooks del sitio web",
          "eyebrow": "Mensaje manual",
          "title": "Panel de difusión",
          "subtitle": "Escribe un mensaje y envíalo directamente a varios canales de Discord configurados.",
          "targets": {
            "eyebrow": "Destinos",
            "title": "Canales de difusión",
            "selectAll": "Seleccionar todos",
            "clearAll": "Borrar selección",
            "empty": "No hay destinos activos. Activa “Disponible para difusiones manuales” en al menos un webhook."
          },
          "message": {
            "eyebrow": "Redactar",
            "title": "Mensaje de Discord"
          },
          "fields": {
            "message": "Mensaje"
          },
          "placeholders": {
            "message": "Escribe un mensaje de Discord con Markdown ..."
          },
          "messageHint": "Se admite Markdown de Discord. Las menciones automáticas están desactivadas.",
          "selected": "{count} canal(es) seleccionado(s)",
          "actions": {
            "send": "Enviar difusión",
            "sending": "Enviando ..."
          },
          "messages": {
            "queued": "Difusión en cola para {count} canal(es)."
          },
          "errors": {
            "load": "No se pudieron cargar los destinos.",
            "send": "No se pudo enviar la difusión."
          }
        }
      }
    }
  },
  "pt": {
    "admin": {
      "tabs": {
        "integrations": "Webhooks do Discord"
      },
      "audit": {
        "entities": {
          "outbound_webhook": "Webhook do Discord"
        }
      },
      "webhooks": {
        "eyebrow": "Automação de canais",
        "title": "Webhooks de canais Discord",
        "subtitle": "Envie eventos selecionados diretamente para canais Discord.",
        "loading": "A carregar webhooks do Discord ...",
        "empty": "Ainda não existem webhooks do Discord.",
        "confirmDelete": "Eliminar o webhook “{name}” e o respetivo histórico?",
        "summary": {
          "total": "Configurados",
          "totalHint": "Todos os destinos Discord",
          "active": "Ativos",
          "activeHint": "Recebem novos eventos",
          "failing": "Requer atenção",
          "failingHint": "A entrega mais recente falhou",
          "deliveries": "Sucesso / falha",
          "deliveriesHint": "Histórico guardado"
        },
        "editor": {
          "eyebrow": "Destino do canal",
          "createTitle": "Criar webhook do Discord",
          "editTitle": "Editar webhook do Discord"
        },
        "fields": {
          "name": "Nome",
          "endpoint": "URL do webhook do Discord",
          "active": "Webhook ativo",
          "scope": "Âmbito",
          "scopeId": "ID do âmbito",
          "discordUsername": "Nome do remetente no Discord",
          "discordAvatar": "URL do avatar do Discord",
          "template": "Modelo da mensagem",
          "events": "Eventos subscritos",
          "broadcastEnabled": "Disponível para transmissões manuais"
        },
        "placeholders": {
          "name": "RBF · Avisos de builds",
          "keepEndpoint": "Deixe vazio para manter o URL secreto atual",
          "template": "Cole um modelo de docs/webhook-templates/message-templates/"
        },
        "endpointHint": "O URL do Discord é tratado como palavra-passe e fica oculto após guardar.",
        "templateHint": "O Discord suporta Markdown. Os marcadores dependem do evento escolhido.",
        "eventsHint": "Escolha os eventos deste canal. O mesmo evento pode ser associado a vários webhooks e canais.",
        "templatePicker": {
          "label": "Preencher com modelo de evento",
          "placeholder": "Escolher um modelo do repositório ...",
          "apply": "Preencher mensagem",
          "useDefaults": "Usar padrões dos eventos",
          "hint": "Escolha um evento para carregar o respetivo modelo inglês versionado. Uma mensagem personalizada aplica-se a todos os eventos subscritos; deixe em branco para usar o padrão de cada evento."
        },
        "eventPicker": {
          "none": "Nenhum evento selecionado",
          "selected": "{count} evento(s) selecionado(s)",
          "summaryHint": "Abrir para gerir subscrições",
          "search": "Pesquisar eventos ...",
          "selectVisible": "Selecionar visíveis",
          "clear": "Limpar",
          "empty": "Nenhum evento correspondente.",
          "remove": "Remover {event}"
        },
        "actions": {
          "create": "Criar webhook",
          "edit": "Editar",
          "test": "Enviar teste",
          "retry": "Tentar novamente"
        },
        "status": {
          "active": "Ativo",
          "inactive": "Inativo",
          "success": "Entregue",
          "failed": "Falhou",
          "queued": "Na fila",
          "processing": "A entregar"
        },
        "scopes": {
          "global": "Geral",
          "fleet": "Frota",
          "squad": "Esquadrão"
        },
        "readOnly": {
          "eyebrow": "Acesso de leitura",
          "title": "Monitor de entregas",
          "hint": "Só administradores podem alterar destinos Discord."
        },
        "list": {
          "eyebrow": "Canais configurados",
          "title": "Subscrições webhook do Discord",
          "events": "eventos",
          "lastSuccess": "Último sucesso",
          "lastFailure": "Última falha",
          "broadcastTarget": "Destino de transmissão"
        },
        "deliveries": {
          "eyebrow": "Monitor de entregas",
          "title": "Entregas recentes ao Discord",
          "allWebhooks": "Todos os webhooks",
          "allStatuses": "Todos os estados",
          "empty": "Ainda não há entregas.",
          "created": "Criado",
          "webhook": "Destino Discord",
          "event": "Evento",
          "status": "Estado",
          "details": "Detalhes"
        },
        "messages": {
          "created": "Webhook do Discord criado.",
          "updated": "Webhook do Discord atualizado.",
          "testSuccess": "Entrega de teste concluída.",
          "testFailed": "O teste falhou. Consulte o histórico.",
          "deleted": "Webhook do Discord eliminado.",
          "retrySuccess": "Nova tentativa concluída.",
          "retryFailed": "A nova tentativa falhou."
        },
        "validation": { "title": "Verifique os dados do webhook.", "name": "Introduza um nome com pelo menos 3 caracteres.", "endpointRequired": "Cole o URL do webhook do Discord.", "endpointInvalid": "Use o URL completo do webhook do canal, incluindo ID e token.", "scope": "Introduza um ID de frota ou esquadrão válido.", "events": "Selecione um evento ou ative as transmissões manuais." },
        "errors": {
          "load": "Não foi possível carregar os webhooks do Discord.",
          "save": "Não foi possível guardar o webhook do Discord.",
          "test": "Não foi possível enviar o teste.",
          "delete": "Não foi possível eliminar o webhook do Discord.",
          "retry": "Não foi possível repetir a entrega."
        },
        "broadcast": {
          "openAutomation": "Webhooks do site",
          "eyebrow": "Mensagem manual",
          "title": "Painel de transmissão",
          "subtitle": "Escreva uma mensagem e envie-a diretamente para vários canais Discord configurados.",
          "targets": {
            "eyebrow": "Destinos",
            "title": "Canais de transmissão",
            "selectAll": "Selecionar todos",
            "clearAll": "Limpar seleção",
            "empty": "Não existem destinos ativos. Ative “Disponível para transmissões manuais” em pelo menos um webhook."
          },
          "message": {
            "eyebrow": "Compor",
            "title": "Mensagem Discord"
          },
          "fields": {
            "message": "Mensagem"
          },
          "placeholders": {
            "message": "Escreva uma mensagem Discord em Markdown ..."
          },
          "messageHint": "O Markdown do Discord é suportado. As menções automáticas estão desativadas.",
          "selected": "{count} canal(is) selecionado(s)",
          "actions": {
            "send": "Enviar transmissão",
            "sending": "A enviar ..."
          },
          "messages": {
            "queued": "Transmissão agendada para {count} canal(is)."
          },
          "errors": {
            "load": "Não foi possível carregar os destinos.",
            "send": "Não foi possível enviar a transmissão."
          }
        }
      }
    }
  },
  "ru": {
    "admin": {
      "tabs": {
        "integrations": "Вебхуки Discord"
      },
      "audit": {
        "entities": {
          "outbound_webhook": "Вебхук Discord"
        }
      },
      "webhooks": {
        "eyebrow": "Автоматизация каналов",
        "title": "Вебхуки каналов Discord",
        "subtitle": "Отправляйте выбранные события напрямую в каналы Discord.",
        "loading": "Загрузка вебхуков Discord ...",
        "empty": "Вебхуки Discord пока не настроены.",
        "confirmDelete": "Удалить вебхук «{name}» и историю доставок?",
        "summary": {
          "total": "Настроено",
          "totalHint": "Все цели Discord",
          "active": "Активны",
          "activeHint": "Получают новые события",
          "failing": "Требуют внимания",
          "failingHint": "Последняя доставка не удалась",
          "deliveries": "Успешно / ошибка",
          "deliveriesHint": "Сохранённая история"
        },
        "editor": {
          "eyebrow": "Цель канала",
          "createTitle": "Создать вебхук Discord",
          "editTitle": "Изменить вебхук Discord"
        },
        "fields": {
          "name": "Название",
          "endpoint": "URL вебхука Discord",
          "active": "Вебхук активен",
          "scope": "Область",
          "scopeId": "ID области",
          "discordUsername": "Имя отправителя Discord",
          "discordAvatar": "URL аватара Discord",
          "template": "Шаблон сообщения",
          "events": "События подписки",
          "broadcastEnabled": "Доступен для ручных рассылок"
        },
        "placeholders": {
          "name": "RBF · Уведомления о билдах",
          "keepEndpoint": "Оставьте пустым, чтобы сохранить текущий секретный URL",
          "template": "Вставьте шаблон из docs/webhook-templates/message-templates/"
        },
        "endpointHint": "URL Discord хранится как пароль и после сохранения маскируется.",
        "templateHint": "Discord поддерживает Markdown. Доступные поля зависят от события.",
        "eventsHint": "Выберите события для канала. Одно событие можно назначить нескольким вебхукам и каналам.",
        "templatePicker": {
          "label": "Заполнить из шаблона события",
          "placeholder": "Выберите шаблон из репозитория ...",
          "apply": "Заполнить сообщение",
          "useDefaults": "Использовать шаблоны событий",
          "hint": "Выберите событие, чтобы загрузить его версионируемый английский шаблон. Пользовательское сообщение применяется ко всем подписанным событиям; оставьте поле пустым для отдельных шаблонов событий."
        },
        "eventPicker": {
          "none": "События не выбраны",
          "selected": "Выбрано событий: {count}",
          "summaryHint": "Открыть управление подписками",
          "search": "Поиск событий ...",
          "selectVisible": "Выбрать видимые",
          "clear": "Очистить",
          "empty": "Подходящих событий нет.",
          "remove": "Удалить {event}"
        },
        "actions": {
          "create": "Создать вебхук",
          "edit": "Изменить",
          "test": "Отправить тест",
          "retry": "Повторить"
        },
        "status": {
          "active": "Активен",
          "inactive": "Неактивен",
          "success": "Доставлено",
          "failed": "Ошибка",
          "queued": "В очереди",
          "processing": "Доставляется"
        },
        "scopes": {
          "global": "Глобально",
          "fleet": "Флот",
          "squad": "Отряд"
        },
        "readOnly": {
          "eyebrow": "Только чтение",
          "title": "Монитор доставок",
          "hint": "Изменять цели Discord могут только администраторы."
        },
        "list": {
          "eyebrow": "Настроенные каналы",
          "title": "Подписки вебхуков Discord",
          "events": "событий",
          "lastSuccess": "Последний успех",
          "lastFailure": "Последняя ошибка",
          "broadcastTarget": "Цель рассылки"
        },
        "deliveries": {
          "eyebrow": "Монитор доставок",
          "title": "Последние доставки Discord",
          "allWebhooks": "Все вебхуки",
          "allStatuses": "Все статусы",
          "empty": "Доставок пока нет.",
          "created": "Создано",
          "webhook": "Цель Discord",
          "event": "Событие",
          "status": "Статус",
          "details": "Подробности"
        },
        "messages": {
          "created": "Вебхук Discord создан.",
          "updated": "Вебхук Discord обновлён.",
          "testSuccess": "Тестовая доставка успешна.",
          "testFailed": "Тест не выполнен. Проверьте историю.",
          "deleted": "Вебхук Discord удалён.",
          "retrySuccess": "Повторная доставка успешна.",
          "retryFailed": "Повторная доставка не удалась."
        },
        "validation": { "title": "Проверьте данные вебхука.", "name": "Введите название не короче 3 символов.", "endpointRequired": "Вставьте URL вебхука Discord.", "endpointInvalid": "Используйте полный URL вебхука канала с ID и токеном.", "scope": "Введите корректный ID флота или отряда.", "events": "Выберите событие или включите ручные рассылки." },
        "errors": {
          "load": "Не удалось загрузить вебхуки Discord.",
          "save": "Не удалось сохранить вебхук Discord.",
          "test": "Не удалось отправить тест.",
          "delete": "Не удалось удалить вебхук Discord.",
          "retry": "Не удалось повторить доставку."
        },
        "broadcast": {
          "openAutomation": "Вебхуки сайта",
          "eyebrow": "Ручное сообщение",
          "title": "Панель рассылки",
          "subtitle": "Создайте одно сообщение и отправьте его сразу в несколько настроенных каналов Discord.",
          "targets": {
            "eyebrow": "Получатели",
            "title": "Каналы рассылки",
            "selectAll": "Выбрать все",
            "clearAll": "Очистить выбор",
            "empty": "Активные цели не настроены. Включите «Доступен для ручных рассылок» хотя бы у одного вебхука."
          },
          "message": {
            "eyebrow": "Сообщение",
            "title": "Сообщение Discord"
          },
          "fields": {
            "message": "Текст"
          },
          "placeholders": {
            "message": "Напишите сообщение Discord с Markdown ..."
          },
          "messageHint": "Поддерживается Markdown Discord. Автоматические упоминания отключены.",
          "selected": "Выбрано каналов: {count}",
          "actions": {
            "send": "Отправить рассылку",
            "sending": "Отправка ..."
          },
          "messages": {
            "queued": "Рассылка поставлена в очередь для каналов: {count}."
          },
          "errors": {
            "load": "Не удалось загрузить цели.",
            "send": "Не удалось отправить рассылку."
          }
        }
      }
    }
  },
  "cn": {
    "admin": {
      "tabs": {
        "integrations": "Discord Webhook"
      },
      "audit": {
        "entities": {
          "outbound_webhook": "Discord Webhook"
        }
      },
      "webhooks": {
        "eyebrow": "频道自动化",
        "title": "Discord 频道 Webhook",
        "subtitle": "将所选网站事件直接发送到 Discord 频道。",
        "loading": "正在加载 Discord Webhook ...",
        "empty": "尚未配置 Discord Webhook。",
        "confirmDelete": "删除 Webhook“{name}”及其投递历史？",
        "summary": {
          "total": "已配置",
          "totalHint": "全部 Discord 目标",
          "active": "活动",
          "activeHint": "接收新事件",
          "failing": "需要处理",
          "failingHint": "最近一次投递失败",
          "deliveries": "成功 / 失败",
          "deliveriesHint": "已保存的投递历史"
        },
        "editor": {
          "eyebrow": "频道目标",
          "createTitle": "创建 Discord Webhook",
          "editTitle": "编辑 Discord Webhook"
        },
        "fields": {
          "name": "名称",
          "endpoint": "Discord Webhook 地址",
          "active": "启用 Webhook",
          "scope": "范围",
          "scopeId": "范围 ID",
          "discordUsername": "Discord 发送者名称",
          "discordAvatar": "Discord 头像地址",
          "template": "消息模板",
          "events": "订阅事件",
          "broadcastEnabled": "可用于手动广播"
        },
        "placeholders": {
          "name": "RBF · 配装通知",
          "keepEndpoint": "留空以保留当前的机密 Discord 地址",
          "template": "从 docs/webhook-templates/message-templates/ 粘贴模板"
        },
        "endpointHint": "Discord 地址按密码处理，保存后会被隐藏。",
        "templateHint": "Discord 支持 Markdown，可用占位符取决于所选事件。",
        "eventsHint": "选择此频道接收的事件。同一事件可以配置到多个 Webhook 和频道。",
        "templatePicker": {
          "label": "从事件模板自动填充",
          "placeholder": "选择仓库模板 ...",
          "apply": "自动填充消息",
          "useDefaults": "使用事件默认模板",
          "hint": "选择事件以载入其版本化英文模板。自定义消息会应用于所有已订阅事件；留空则使用每个事件自己的默认模板。"
        },
        "eventPicker": {
          "none": "未选择事件",
          "selected": "已选择 {count} 个事件",
          "summaryHint": "打开以管理订阅",
          "search": "搜索事件 ...",
          "selectVisible": "选择可见项",
          "clear": "清除",
          "empty": "没有匹配的事件。",
          "remove": "移除 {event}"
        },
        "actions": {
          "create": "创建 Webhook",
          "edit": "编辑",
          "test": "发送测试",
          "retry": "重试"
        },
        "status": {
          "active": "活动",
          "inactive": "停用",
          "success": "已投递",
          "failed": "失败",
          "queued": "排队中",
          "processing": "投递中"
        },
        "scopes": {
          "global": "全局",
          "fleet": "舰队",
          "squad": "小队"
        },
        "readOnly": {
          "eyebrow": "只读访问",
          "title": "投递监控",
          "hint": "只有管理员可以更改 Discord Webhook 目标。"
        },
        "list": {
          "eyebrow": "已配置频道",
          "title": "Discord Webhook 订阅",
          "events": "个事件",
          "lastSuccess": "最近成功",
          "lastFailure": "最近失败",
          "broadcastTarget": "广播目标"
        },
        "deliveries": {
          "eyebrow": "投递监控",
          "title": "最近的 Discord 投递",
          "allWebhooks": "全部 Webhook",
          "allStatuses": "全部状态",
          "empty": "尚无投递记录。",
          "created": "创建时间",
          "webhook": "Discord 目标",
          "event": "事件",
          "status": "状态",
          "details": "详情"
        },
        "messages": {
          "created": "Discord Webhook 已创建。",
          "updated": "Discord Webhook 已更新。",
          "testSuccess": "测试投递成功。",
          "testFailed": "测试投递失败，请查看历史。",
          "deleted": "Discord Webhook 已删除。",
          "retrySuccess": "重试成功。",
          "retryFailed": "重试失败。"
        },
        "validation": { "title": "请检查 Webhook 信息。", "name": "请输入至少 3 个字符的名称。", "endpointRequired": "请粘贴 Discord Webhook URL。", "endpointInvalid": "请使用包含 ID 和令牌的完整频道 Webhook URL。", "scope": "请输入有效的舰队或小队 ID。", "events": "请选择至少一个事件或启用手动广播。" },
        "errors": {
          "load": "无法加载 Discord Webhook。",
          "save": "无法保存 Discord Webhook。",
          "test": "无法发送测试。",
          "delete": "无法删除 Discord Webhook。",
          "retry": "无法重试投递。"
        },
        "broadcast": {
          "openAutomation": "网站 Webhook",
          "eyebrow": "手动频道消息",
          "title": "广播面板",
          "subtitle": "编写一条消息并同时直接发送到多个已配置的 Discord 频道。",
          "targets": {
            "eyebrow": "目标",
            "title": "广播频道",
            "selectAll": "全选",
            "clearAll": "清除选择",
            "empty": "尚未配置活动广播目标。请至少为一个 Webhook 启用“可用于手动广播”。"
          },
          "message": {
            "eyebrow": "编写",
            "title": "Discord 消息"
          },
          "fields": {
            "message": "消息"
          },
          "placeholders": {
            "message": "编写 Discord Markdown 消息 ..."
          },
          "messageHint": "支持 Discord Markdown。出于安全考虑，自动提及已禁用。",
          "selected": "已选择 {count} 个频道",
          "actions": {
            "send": "发送广播",
            "sending": "正在发送 ..."
          },
          "messages": {
            "queued": "广播已加入 {count} 个频道的发送队列。"
          },
          "errors": {
            "load": "无法加载广播目标。",
            "send": "无法发送广播。"
          }
        }
      }
    }
  }
}
