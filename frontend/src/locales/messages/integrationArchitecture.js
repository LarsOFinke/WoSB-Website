export const integrationArchitectureMessages = {
  en: {
    botSetup: {
      tabs: { label: 'Discord integration areas', bot: 'Bot', chatWebhooks: 'Chat webhooks' },
      bot: { eyebrow: 'Advanced Discord bot', title: 'Install and operate the bot', text: 'This area contains only bot installation, credentials and runtime controls. Channel routing belongs to chat webhooks.' },
      chatWebhooks: { eyebrow: 'Direct backend delivery', title: 'Discord chat webhooks and event subscriptions', text: 'Send website events directly to channel-bound Discord webhook URLs without a second repository. Signed JSON subscriptions remain available for advanced integrations.', directTitle: 'Direct Discord delivery', directText: 'The backend renders and sends the message to the Discord webhook URL.', eventsTitle: 'Extensible events', eventsText: 'Registrations, squads and later modules use the same event catalog and delivery history.', scopesTitle: 'Global, fleet or squad', scopesText: 'A subscription can receive all events or only events from one fleet or squad.' },
    },
    admin: { webhooks: {
      summary: { discordHint: 'Direct Discord chat destinations', signedHint: 'Advanced signed JSON receivers' },
      fields: { mode: 'Delivery type', scope: 'Scope', scopeId: 'Scope ID', discordUsername: 'Discord sender name', discordAvatar: 'Discord avatar URL' },
      modes: { discord: 'Discord chat webhook', signed_json: 'Signed JSON webhook' },
      scopes: { global: 'Global', fleet: 'Fleet', squad: 'Squad' },
      placeholders: { keepEndpoint: 'Leave blank to keep the configured Discord URL' },
      templateHint: 'Available placeholders include {event}, {data.title}, {resource.id} and {resource.url}.',
    } },
    fleets: { manage: {
      tabs: { roles: 'Roles' },
      roles: { title: 'Fleet roles', subtitle: 'Fleet admirals define additional roles below the protected admiral role.', editor: 'Role editor', create: 'Create role', edit: 'Edit role', code: 'Technical code', label: 'Display name', rank: 'Rank', rankHint: '1–79. Higher ranks may manage lower ranks when member management is enabled.', leadership: 'Leadership role', manageFleet: 'May manage fleet profile', manageMembers: 'May manage members', active: 'Role active', catalog: 'Role catalog', available: 'Available roles', system: 'System role', custom: 'Custom role', members: 'members', saved: 'Fleet role saved.', deleted: 'Fleet role deleted.', error: 'Fleet role could not be changed.', confirmDelete: 'Delete fleet role “{role}”?' },
    } },
  },
  de: {
    botSetup: {
      tabs: { label: 'Discord-Integrationsbereiche', bot: 'Discord-Bot', chatWebhooks: 'Chat-Webhooks' },
      bot: { eyebrow: 'Erweiterter Discord-Bot', title: 'Bot installieren und betreiben', text: 'Dieser Bereich enthält ausschließlich Bot-Installation, Zugangsdaten und Laufzeitsteuerung. Channel-Routing wird über Chat-Webhooks konfiguriert.' },
      chatWebhooks: { eyebrow: 'Direkte Backend-Zustellung', title: 'Discord-Chat-Webhooks und Event-Abonnements', text: 'Website-Events werden ohne zweites Repository direkt an channelgebundene Discord-Webhook-URLs gesendet. Signierte JSON-Abonnements bleiben für erweiterte Integrationen verfügbar.', directTitle: 'Direkte Discord-Zustellung', directText: 'Das Backend rendert die Nachricht und sendet sie an die Discord-Webhook-URL.', eventsTitle: 'Erweiterbarer Event-Katalog', eventsText: 'Registrierungen, Squads und spätere Module verwenden denselben Event-Katalog und dieselbe Zustellhistorie.', scopesTitle: 'Global, Flotte oder Squad', scopesText: 'Ein Abonnement kann alle Events oder nur Events einer bestimmten Flotte beziehungsweise eines Squads empfangen.' },
    },
    admin: { webhooks: {
      summary: { discordHint: 'Direkte Discord-Chat-Ziele', signedHint: 'Erweiterte signierte JSON-Receiver' },
      fields: { mode: 'Zustelltyp', scope: 'Gültigkeitsbereich', scopeId: 'Bereichs-ID', discordUsername: 'Discord-Absendername', discordAvatar: 'Discord-Avatar-URL' },
      modes: { discord: 'Discord-Chat-Webhook', signed_json: 'Signierter JSON-Webhook' },
      scopes: { global: 'Übergreifend', fleet: 'Flotte', squad: 'Einsatzgruppe' },
      placeholders: { keepEndpoint: 'Leer lassen, um die konfigurierte Discord-URL beizubehalten' },
      templateHint: 'Verfügbare Platzhalter sind unter anderem {event}, {data.title}, {resource.id} und {resource.url}.',
    } },
    fleets: { manage: {
      tabs: { roles: 'Rollen' },
      roles: { title: 'Flottenrollen', subtitle: 'Flottenadmiräle definieren zusätzliche Rollen unterhalb der geschützten Admiralsrolle.', editor: 'Rolleneditor', create: 'Rolle anlegen', edit: 'Rolle bearbeiten', code: 'Technischer Code', label: 'Anzeigename', rank: 'Rang', rankHint: '1–79. Höhere Ränge können niedrigere verwalten, wenn Mitgliederverwaltung aktiviert ist.', leadership: 'Führungsrolle', manageFleet: 'Darf Flottenprofil verwalten', manageMembers: 'Darf Mitglieder verwalten', active: 'Rolle aktiv', catalog: 'Rollenkatalog', available: 'Verfügbare Rollen', system: 'Systemrolle', custom: 'Eigene Rolle', members: 'Mitglieder', saved: 'Flottenrolle gespeichert.', deleted: 'Flottenrolle gelöscht.', error: 'Flottenrolle konnte nicht geändert werden.', confirmDelete: 'Flottenrolle „{role}“ löschen?' },
    } },
  },

  fr: {
    botSetup: {
      tabs: { bot: 'Robot Discord', chatWebhooks: 'Webhooks de discussion' },
      chatWebhooks: { eyebrow: 'Livraison directe par le serveur' },
    },
    admin: { webhooks: {
      summary: { signedHint: 'Récepteurs JSON signés avancés' },
      fields: { mode: 'Type de livraison', scope: 'Portée', scopeId: 'Identifiant de portée' },
      modes: { signed_json: 'Webhook JSON signé' },
      scopes: { global: 'Portée globale', squad: 'Escouade' },
    } },
    fleets: { manage: { roles: { code: 'Code technique', rank: 'Niveau hiérarchique' } } },
  },
  es: {
    botSetup: {
      tabs: { bot: 'Bot de Discord', chatWebhooks: 'Webhooks de chat' },
      chatWebhooks: { eyebrow: 'Entrega directa desde el servidor' },
    },
    admin: { webhooks: {
      summary: { signedHint: 'Receptores JSON firmados avanzados' },
      fields: { mode: 'Tipo de entrega', scope: 'Ámbito', scopeId: 'ID del ámbito' },
      modes: { signed_json: 'Webhook JSON firmado' },
      scopes: { global: 'Ámbito global', squad: 'Escuadrón' },
    } },
    fleets: { manage: { roles: { code: 'Código técnico', rank: 'Nivel jerárquico' } } },
  },
  pt: {
    botSetup: {
      tabs: { bot: 'Bot do Discord', chatWebhooks: 'Webhooks de chat' },
      chatWebhooks: { eyebrow: 'Entrega direta pelo servidor' },
    },
    admin: { webhooks: {
      summary: { signedHint: 'Recetores JSON assinados avançados' },
      fields: { mode: 'Tipo de entrega', scope: 'Âmbito', scopeId: 'ID do âmbito' },
      modes: { signed_json: 'Webhook JSON assinado' },
      scopes: { global: 'Âmbito global', squad: 'Esquadrão' },
    } },
    fleets: { manage: { roles: { code: 'Código técnico', rank: 'Nível hierárquico' } } },
  },
  ru: {
    botSetup: {
      tabs: { bot: 'Discord-бот', chatWebhooks: 'Чат-вебхуки' },
      chatWebhooks: { eyebrow: 'Прямая отправка сервером' },
    },
    admin: { webhooks: {
      summary: { signedHint: 'Расширенные получатели подписанного JSON' },
      fields: { mode: 'Тип доставки', scope: 'Область действия', scopeId: 'ID области' },
      modes: { signed_json: 'Подписанный JSON-вебхук' },
      scopes: { global: 'Общая область', squad: 'Отряд' },
    } },
    fleets: { manage: { roles: { code: 'Технический код', rank: 'Уровень роли' } } },
  },
  cn: {
    botSetup: {
      tabs: { bot: 'Discord 机器人', chatWebhooks: '聊天 Webhook' },
      chatWebhooks: { eyebrow: '由服务器直接投递' },
    },
    admin: { webhooks: {
      summary: { signedHint: '高级签名 JSON 接收端' },
      fields: { mode: '投递类型', scope: '作用范围', scopeId: '范围 ID' },
      modes: { signed_json: '签名 JSON Webhook' },
      scopes: { global: '全局范围', squad: '小队' },
    } },
    fleets: { manage: { roles: { code: '技术代码', rank: '角色等级' } } },
  },
}
