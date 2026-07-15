export const discordIntegrationSeparationMessages = {
  en: {
    botSetup: {
      navigation: 'Discord bot', eyebrow: 'Discord bot', title: 'Discord bot management',
      subtitle: 'Install, configure and operate the optional Discord bot independently from direct Discord webhooks.',
      bot: { eyebrow: 'Bot runtime', title: 'Installation and operation', text: 'This page contains only bot credentials, installation, updates and runtime controls. Event destinations and channel messages are managed separately under Discord webhooks.' },
    },
    webhookSetup: {
      navigation: 'Discord webhooks', eyebrow: 'Webhook administration', title: 'Discord webhooks and signed integrations',
      subtitle: 'Manage direct Discord channel webhooks and signed JSON subscriptions independently from the Discord bot runtime.',
      delivery: { eyebrow: 'Two independent delivery modes', title: 'Direct channel messages or signed integration events', text: 'Both modes use the same event catalog, scopes, delivery history and retry controls, but they operate independently.', directTitle: 'Discord chat webhook', directText: 'The website backend renders the message and posts it directly to a native Discord channel webhook. No bot repository is required.', signedTitle: 'Signed JSON webhook', signedText: 'The website sends a signed event envelope to the bot or another integration service, which handles routing and rendering.', scopesTitle: 'Global, fleet or squad', scopesText: 'Subscriptions can receive every event or only events belonging to one fleet or squad.' },
      templates: { eyebrow: 'Copy-ready templates', title: 'Versioned message templates in the repository', text: 'Ready-to-copy templates for every supported event are stored as plain text files. Copy a file into the message template field and adjust it as needed.' },
    },
  },
  de: {
    botSetup: {
      navigation: 'Discord-Bot', eyebrow: 'Discord-Bot', title: 'Discord-Bot-Verwaltung',
      subtitle: 'Den optionalen Discord-Bot unabhängig von direkten Discord-Webhooks installieren, konfigurieren und betreiben.',
      bot: { eyebrow: 'Bot-Laufzeit', title: 'Installation und Betrieb', text: 'Diese Seite enthält ausschließlich Bot-Zugangsdaten, Installation, Updates und Laufzeitsteuerung. Event-Ziele und Channel-Nachrichten werden getrennt unter Discord-Webhooks verwaltet.' },
    },
    webhookSetup: {
      navigation: 'Discord-Webhooks', eyebrow: 'Webhook-Verwaltung', title: 'Discord-Webhooks und signierte Integrationen',
      subtitle: 'Direkte Discord-Channel-Webhooks und signierte JSON-Abonnements unabhängig von der Discord-Bot-Laufzeit verwalten.',
      delivery: { eyebrow: 'Zwei unabhängige Zustellarten', title: 'Direkte Channel-Nachricht oder signiertes Integrations-Event', text: 'Beide Zustellarten verwenden denselben Event-Katalog, dieselben Scopes, dieselbe Historie und dieselben Wiederholungsfunktionen, arbeiten aber unabhängig voneinander.', directTitle: 'Discord-Chat-Webhook', directText: 'Das Website-Backend rendert die Nachricht und sendet sie direkt an einen nativen Discord-Channel-Webhook. Das Bot-Repository wird dafür nicht benötigt.', signedTitle: 'Signierter JSON-Webhook', signedText: 'Die Website sendet einen signierten Event-Envelope an den Bot oder einen anderen Integrationsdienst, der Routing und Darstellung übernimmt.', scopesTitle: 'Global, Flotte oder Squad', scopesText: 'Abonnements können alle Events oder nur Events einer bestimmten Flotte beziehungsweise eines Squads empfangen.' },
      templates: { eyebrow: 'Vorlagen zum Kopieren', title: 'Versionierte Nachrichten-Templates im Repository', text: 'Für jedes unterstützte Event liegen direkt kopierbare Klartextdateien bereit. Den Inhalt einfach in das Feld Nachrichten-Template einfügen und bei Bedarf anpassen.' },
    },
  },
  fr: {
    botSetup: {
      navigation: 'Bot Discord', eyebrow: 'Bot Discord', title: 'Gestion du bot Discord',
      subtitle: 'Installer, configurer et exploiter le bot Discord optionnel indépendamment des webhooks Discord directs.',
      bot: { eyebrow: 'Exécution du bot', title: 'Installation et exploitation', text: 'Cette page contient uniquement les identifiants, l’installation, les mises à jour et les contrôles d’exécution du bot. Les destinations et messages sont gérés séparément dans les webhooks Discord.' },
    },
    webhookSetup: {
      navigation: 'Webhooks Discord', eyebrow: 'Administration des webhooks', title: 'Webhooks Discord et intégrations signées',
      subtitle: 'Gérer les webhooks de salon Discord et les abonnements JSON signés indépendamment du bot Discord.',
      delivery: { eyebrow: 'Deux modes indépendants', title: 'Message direct ou événement signé', text: 'Les deux modes partagent le catalogue d’événements, les portées, l’historique et les nouvelles tentatives, tout en restant indépendants.', directTitle: 'Webhook de discussion Discord', directText: 'Le serveur du site rend le message et l’envoie directement à un webhook de salon Discord, sans dépôt de bot.', signedTitle: 'Webhook JSON signé', signedText: 'Le site envoie une enveloppe signée au bot ou à un autre service qui assure le routage et le rendu.', scopesTitle: 'Global, flotte ou escouade', scopesText: 'Un abonnement peut recevoir tous les événements ou seulement ceux d’une flotte ou d’une escouade.' },
      templates: { eyebrow: 'Modèles à copier', title: 'Modèles versionnés dans le dépôt', text: 'Un fichier texte prêt à copier existe pour chaque événement. Copiez son contenu dans le champ de modèle puis adaptez-le.' },
    },
  },
  es: {
    botSetup: {
      navigation: 'Bot de Discord', eyebrow: 'Bot de Discord', title: 'Gestión del bot de Discord',
      subtitle: 'Instala, configura y opera el bot opcional de forma independiente de los webhooks directos de Discord.',
      bot: { eyebrow: 'Ejecución del bot', title: 'Instalación y operación', text: 'Esta página contiene únicamente credenciales, instalación, actualizaciones y controles del bot. Los destinos y mensajes se administran por separado en Webhooks de Discord.' },
    },
    webhookSetup: {
      navigation: 'Webhooks de Discord', eyebrow: 'Administración de webhooks', title: 'Webhooks de Discord e integraciones firmadas',
      subtitle: 'Gestiona webhooks directos de canales y suscripciones JSON firmadas independientemente del bot.',
      delivery: { eyebrow: 'Dos modos independientes', title: 'Mensaje directo o evento firmado', text: 'Ambos modos comparten catálogo, ámbitos, historial y reintentos, pero funcionan de forma independiente.', directTitle: 'Webhook de chat de Discord', directText: 'El backend renderiza el mensaje y lo envía directamente a un webhook nativo del canal, sin repositorio del bot.', signedTitle: 'Webhook JSON firmado', signedText: 'El sitio envía un sobre firmado al bot u otro servicio, que se encarga del enrutamiento y la presentación.', scopesTitle: 'Global, flota o escuadrón', scopesText: 'Una suscripción puede recibir todos los eventos o solo los de una flota o escuadrón.' },
      templates: { eyebrow: 'Plantillas para copiar', title: 'Plantillas versionadas en el repositorio', text: 'Hay un archivo de texto listo para copiar para cada evento. Copia su contenido en el campo de plantilla y ajústalo.' },
    },
  },
  pt: {
    botSetup: {
      navigation: 'Bot do Discord', eyebrow: 'Bot do Discord', title: 'Gestão do bot Discord',
      subtitle: 'Instalar, configurar e operar o bot opcional independentemente dos webhooks diretos do Discord.',
      bot: { eyebrow: 'Execução do bot', title: 'Instalação e operação', text: 'Esta página contém apenas credenciais, instalação, atualizações e controlos do bot. Destinos e mensagens são geridos separadamente nos Webhooks do Discord.' },
    },
    webhookSetup: {
      navigation: 'Webhooks do Discord', eyebrow: 'Administração de webhooks', title: 'Webhooks do Discord e integrações assinadas',
      subtitle: 'Gerir webhooks diretos de canais e subscrições JSON assinadas independentemente do bot.',
      delivery: { eyebrow: 'Dois modos independentes', title: 'Mensagem direta ou evento assinado', text: 'Os dois modos partilham catálogo, âmbitos, histórico e novas tentativas, mas funcionam de forma independente.', directTitle: 'Webhook de chat do Discord', directText: 'O backend renderiza a mensagem e envia-a diretamente para um webhook nativo do canal, sem o repositório do bot.', signedTitle: 'Webhook JSON assinado', signedText: 'O site envia um envelope assinado ao bot ou a outro serviço, que trata do encaminhamento e da apresentação.', scopesTitle: 'Global, frota ou esquadrão', scopesText: 'Uma subscrição pode receber todos os eventos ou apenas os de uma frota ou esquadrão.' },
      templates: { eyebrow: 'Modelos para copiar', title: 'Modelos versionados no repositório', text: 'Existe um ficheiro de texto pronto a copiar para cada evento. Copie o conteúdo para o campo de modelo e adapte-o.' },
    },
  },
  ru: {
    botSetup: {
      navigation: 'Discord-бот', eyebrow: 'Discord-бот', title: 'Управление Discord-ботом',
      subtitle: 'Устанавливайте, настраивайте и запускайте дополнительного бота отдельно от прямых Discord-вебхуков.',
      bot: { eyebrow: 'Среда бота', title: 'Установка и работа', text: 'На этой странице находятся только учётные данные, установка, обновления и управление процессом бота. Цели и сообщения настраиваются отдельно в разделе Discord-вебхуков.' },
    },
    webhookSetup: {
      navigation: 'Discord-вебхуки', eyebrow: 'Управление вебхуками', title: 'Discord-вебхуки и подписанные интеграции',
      subtitle: 'Управляйте прямыми вебхуками каналов и подписанными JSON-подписками независимо от бота.',
      delivery: { eyebrow: 'Два независимых режима', title: 'Прямое сообщение или подписанное событие', text: 'Оба режима используют общий каталог, области, историю и повторы, но работают независимо.', directTitle: 'Чат-вебхук Discord', directText: 'Сервер сайта формирует сообщение и отправляет его прямо в вебхук канала Discord без репозитория бота.', signedTitle: 'Подписанный JSON-вебхук', signedText: 'Сайт отправляет подписанный конверт боту или другому сервису, который выполняет маршрутизацию и отображение.', scopesTitle: 'Глобально, флот или отряд', scopesText: 'Подписка может получать все события либо события выбранного флота или отряда.' },
      templates: { eyebrow: 'Шаблоны для копирования', title: 'Версионируемые шаблоны в репозитории', text: 'Для каждого события есть готовый текстовый файл. Скопируйте его в поле шаблона и при необходимости измените.' },
    },
  },
  cn: {
    botSetup: {
      navigation: 'Discord 机器人', eyebrow: 'Discord 机器人', title: 'Discord 机器人管理',
      subtitle: '独立于直接 Discord Webhook 安装、配置和运行可选机器人。',
      bot: { eyebrow: '机器人运行环境', title: '安装与运行', text: '此页面仅包含机器人凭据、安装、更新和运行控制。事件目标与频道消息在 Discord Webhook 中单独管理。' },
    },
    webhookSetup: {
      navigation: 'Discord Webhook', eyebrow: 'Webhook 管理', title: 'Discord Webhook 与签名集成',
      subtitle: '独立于机器人运行环境管理频道 Webhook 和签名 JSON 订阅。',
      delivery: { eyebrow: '两种独立投递方式', title: '直接频道消息或签名事件', text: '两种方式共用事件目录、范围、历史记录和重试功能，但彼此独立运行。', directTitle: 'Discord 聊天 Webhook', directText: '网站后端直接渲染消息并发送到 Discord 频道原生 Webhook，无需机器人仓库。', signedTitle: '签名 JSON Webhook', signedText: '网站向机器人或其他集成服务发送签名事件信封，由接收方处理路由和展示。', scopesTitle: '全局、舰队或小队', scopesText: '订阅可以接收全部事件，或只接收指定舰队或小队的事件。' },
      templates: { eyebrow: '可复制模板', title: '仓库中的版本化消息模板', text: '每个事件都有可直接复制的文本文件。将内容复制到消息模板字段后按需调整。' },
    },
  },
}
