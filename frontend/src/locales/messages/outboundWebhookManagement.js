export const outboundWebhookManagementMessages = {
  en: {
    admin: {
      tabs: { integrations: 'Integrations' },
      audit: { entities: { outbound_webhook: 'Outbound webhook' } },
      webhooks: {
        eyebrow: 'External automation',
        title: 'Outbound webhooks',
        subtitle: 'Send signed project events to your Discord bot or another integration service.',
        loading: 'Loading integrations ...',
        empty: 'No outbound webhooks configured yet.',
        confirmDelete: 'Delete webhook “{name}” and its delivery history?',
        summary: {
          total: 'Configured', totalHint: 'All webhook endpoints',
          active: 'Active', activeHint: 'Receiving new events',
          failing: 'Needs attention', failingHint: 'Latest delivery failed',
          deliveries: 'Success / failed', deliveriesHint: 'Persisted delivery history',
        },
        editor: { eyebrow: 'Endpoint configuration', createTitle: 'Create integration', editTitle: 'Edit integration' },
        fields: { name: 'Name', endpoint: 'Bot endpoint URL', channelKey: 'Channel key', active: 'Integration active', template: 'Optional message template', events: 'Subscribed events' },
        placeholders: { name: 'Discord bot · Events', channelKey: 'events, guides, builds ...', template: 'Optional routing or formatting hint for the bot' },
        eventsHint: 'Create separate integrations when different event groups should reach different Discord channels.',
        actions: { create: 'Create webhook', edit: 'Edit', test: 'Send test', rotate: 'Rotate secret', retry: 'Retry' },
        status: { active: 'Active', inactive: 'Inactive', success: 'Delivered', failed: 'Failed', queued: 'Queued' },
        secret: { oneTime: 'Copy this signing secret now', hint: 'The full secret is shown only after creation or rotation. Your bot uses it to verify X-RBF-Signature.', copy: 'Copy secret' },
        readOnly: { eyebrow: 'Read-only access', title: 'Integration monitoring', hint: 'Moderators can inspect endpoints and deliveries. Only administrators can create, change or delete integrations.' },
        list: { eyebrow: 'Configured endpoints', title: 'Webhook subscriptions', noChannel: 'No channel key', events: 'events', secret: 'Secret', lastSuccess: 'Last success', lastFailure: 'Last failure' },
        deliveries: { eyebrow: 'Delivery monitor', title: 'Recent webhook deliveries', allWebhooks: 'All webhooks', allStatuses: 'All statuses', empty: 'No webhook deliveries recorded yet.', created: 'Created', webhook: 'Webhook', event: 'Event', resource: 'Resource', status: 'Status', attempts: 'Attempts', details: 'Details' },
        messages: { created: 'Webhook created.', updated: 'Webhook updated.', testSuccess: 'Test delivery succeeded.', testFailed: 'Test delivery failed. Check the delivery history.', rotated: 'Signing secret rotated.', deleted: 'Webhook deleted.', retrySuccess: 'Delivery retry succeeded.', retryFailed: 'Delivery retry failed.', secretCopied: 'Signing secret copied.' },
        errors: { load: 'Integrations could not be loaded.', save: 'Webhook could not be saved.', test: 'Test delivery could not be sent.', rotate: 'Signing secret could not be rotated.', delete: 'Webhook could not be deleted.', retry: 'Delivery could not be retried.' },
      },
    },
  },
  de: {
    admin: {
      tabs: { integrations: 'Integrationen' },
      audit: { entities: { outbound_webhook: 'Ausgehender Webhook' } },
      webhooks: {
        eyebrow: 'Externe Automatisierung',
        title: 'Ausgehende Webhooks',
        subtitle: 'Sende signierte Projekt-Ereignisse an deinen Discord-Bot oder einen anderen Integrationsdienst.',
        loading: 'Integrationen werden geladen ...',
        empty: 'Noch keine ausgehenden Webhooks eingerichtet.',
        confirmDelete: 'Webhook „{name}“ samt Zustellhistorie löschen?',
        summary: {
          total: 'Eingerichtet', totalHint: 'Alle Webhook-Endpunkte',
          active: 'Aktiv', activeHint: 'Empfangen neue Ereignisse',
          failing: 'Prüfung nötig', failingHint: 'Letzte Zustellung fehlgeschlagen',
          deliveries: 'Erfolgreich / fehlgeschlagen', deliveriesHint: 'Gespeicherte Zustellhistorie',
        },
        editor: { eyebrow: 'Endpunkt-Konfiguration', createTitle: 'Integration anlegen', editTitle: 'Integration bearbeiten' },
        fields: { name: 'Bezeichnung', endpoint: 'Endpunkt-URL des Bots', channelKey: 'Channel-Schlüssel', active: 'Integration aktiv', template: 'Optionale Nachrichtenvorlage', events: 'Abonnierte Ereignisse' },
        placeholders: { name: 'Discord-Bot · Events', channelKey: 'events, guides, builds ...', template: 'Optionale Routing- oder Formatierungsvorgabe für den Bot' },
        eventsHint: 'Lege getrennte Integrationen an, wenn verschiedene Ereignisgruppen in unterschiedliche Discord-Channels sollen.',
        actions: { create: 'Webhook anlegen', edit: 'Bearbeiten', test: 'Test senden', rotate: 'Secret rotieren', retry: 'Erneut senden' },
        status: { active: 'Aktiv', inactive: 'Inaktiv', success: 'Zugestellt', failed: 'Fehlgeschlagen', queued: 'Wartend' },
        secret: { oneTime: 'Signatur-Secret jetzt kopieren', hint: 'Das vollständige Secret wird nur nach Erstellung oder Rotation angezeigt. Der Bot prüft damit X-RBF-Signature.', copy: 'Secret kopieren' },
        readOnly: { eyebrow: 'Nur-Lese-Zugriff', title: 'Integrations-Monitoring', hint: 'Moderatoren können Endpunkte und Zustellungen einsehen. Nur Administratoren dürfen Integrationen anlegen, ändern oder löschen.' },
        list: { eyebrow: 'Eingerichtete Endpunkte', title: 'Webhook-Abonnements', noChannel: 'Kein Channel-Schlüssel', events: 'Ereignisse', secret: 'Signaturschlüssel', lastSuccess: 'Letzter Erfolg', lastFailure: 'Letzter Fehler' },
        deliveries: { eyebrow: 'Zustell-Monitor', title: 'Letzte Webhook-Zustellungen', allWebhooks: 'Alle Webhooks', allStatuses: 'Alle Status', empty: 'Noch keine Webhook-Zustellungen vorhanden.', created: 'Erstellt', webhook: 'Integration', event: 'Ereignis', resource: 'Ressource', status: 'Status', attempts: 'Versuche', details: 'Details' },
        messages: { created: 'Webhook angelegt.', updated: 'Webhook aktualisiert.', testSuccess: 'Testzustellung erfolgreich.', testFailed: 'Testzustellung fehlgeschlagen. Bitte Zustellhistorie prüfen.', rotated: 'Signatur-Secret rotiert.', deleted: 'Webhook gelöscht.', retrySuccess: 'Erneute Zustellung erfolgreich.', retryFailed: 'Erneute Zustellung fehlgeschlagen.', secretCopied: 'Signatur-Secret kopiert.' },
        errors: { load: 'Integrationen konnten nicht geladen werden.', save: 'Webhook konnte nicht gespeichert werden.', test: 'Testzustellung konnte nicht gesendet werden.', rotate: 'Signatur-Secret konnte nicht rotiert werden.', delete: 'Webhook konnte nicht gelöscht werden.', retry: 'Zustellung konnte nicht wiederholt werden.' },
      },
    },
  },
  fr: {
    admin: {
      tabs: { integrations: 'Intégrations' },
      audit: { entities: { outbound_webhook: 'Webhook sortant' } },
      webhooks: {
        eyebrow: 'Automatisation externe', title: 'Webhooks sortants', subtitle: 'Envoyez des événements signés au bot Discord ou à un autre service.', loading: 'Chargement des intégrations ...', empty: 'Aucun webhook sortant configuré.', confirmDelete: 'Supprimer le webhook « {name} » et son historique ?',
        summary: { total: 'Configurés', totalHint: 'Tous les points de terminaison', active: 'Actifs', activeHint: 'Reçoivent de nouveaux événements', failing: 'À vérifier', failingHint: 'Dernière livraison en échec', deliveries: 'Succès / échecs', deliveriesHint: 'Historique enregistré' },
        editor: { eyebrow: 'Configuration du point de terminaison', createTitle: 'Créer une intégration', editTitle: 'Modifier l’intégration' },
        fields: { name: 'Nom', endpoint: 'URL du bot', channelKey: 'Clé de canal', active: 'Intégration active', template: 'Modèle de message facultatif', events: 'Événements abonnés' },
        placeholders: { name: 'Bot Discord · Événements', channelKey: 'events, guides, builds ...', template: 'Indication facultative de routage ou de formatage' },
        eventsHint: 'Créez des intégrations séparées pour distribuer les groupes vers différents salons Discord.', actions: { create: 'Créer le webhook', edit: 'Modifier', test: 'Envoyer un test', rotate: 'Renouveler le secret', retry: 'Réessayer' }, status: { active: 'Actif', inactive: 'Inactif', success: 'Livré', failed: 'Échec', queued: 'En attente' },
        secret: { oneTime: 'Copiez maintenant le secret de signature', hint: 'Le secret complet apparaît uniquement après création ou renouvellement.', copy: 'Copier le secret' }, readOnly: { eyebrow: 'Accès en lecture', title: 'Suivi des intégrations', hint: 'Les modérateurs consultent les points et livraisons. Seuls les administrateurs peuvent les modifier.' },
        list: { eyebrow: 'Points configurés', title: 'Abonnements webhook', noChannel: 'Aucune clé de canal', events: 'événements', secret: 'Clé de signature', lastSuccess: 'Dernier succès', lastFailure: 'Dernier échec' }, deliveries: { eyebrow: 'Suivi des livraisons', title: 'Livraisons webhook récentes', allWebhooks: 'Tous les webhooks', allStatuses: 'Tous les états', empty: 'Aucune livraison enregistrée.', created: 'Créé', webhook: 'Intégration', event: 'Événement', resource: 'Ressource', status: 'État', attempts: 'Tentatives', details: 'Détails' },
        messages: { created: 'Webhook créé.', updated: 'Webhook mis à jour.', testSuccess: 'Test réussi.', testFailed: 'Test échoué. Consultez l’historique.', rotated: 'Secret renouvelé.', deleted: 'Webhook supprimé.', retrySuccess: 'Nouvelle tentative réussie.', retryFailed: 'Nouvelle tentative échouée.', secretCopied: 'Secret copié.' }, errors: { load: 'Impossible de charger les intégrations.', save: 'Impossible d’enregistrer le webhook.', test: 'Impossible d’envoyer le test.', rotate: 'Impossible de renouveler le secret.', delete: 'Impossible de supprimer le webhook.', retry: 'Impossible de réessayer la livraison.' },
      },
    },
  },
  es: {
    admin: {
      tabs: { integrations: 'Integraciones' }, audit: { entities: { outbound_webhook: 'Webhook saliente' } },
      webhooks: {
        eyebrow: 'Automatización externa', title: 'Webhooks salientes', subtitle: 'Envía eventos firmados al bot de Discord u otro servicio.', loading: 'Cargando integraciones ...', empty: 'No hay webhooks salientes configurados.', confirmDelete: '¿Eliminar el webhook «{name}» y su historial?',
        summary: { total: 'Configurados', totalHint: 'Todos los endpoints', active: 'Activos', activeHint: 'Reciben eventos nuevos', failing: 'Requieren atención', failingHint: 'La última entrega falló', deliveries: 'Éxitos / fallos', deliveriesHint: 'Historial guardado' }, editor: { eyebrow: 'Configuración del endpoint', createTitle: 'Crear integración', editTitle: 'Editar integración' },
        fields: { name: 'Nombre', endpoint: 'URL del bot', channelKey: 'Clave de canal', active: 'Integración activa', template: 'Plantilla opcional', events: 'Eventos suscritos' }, placeholders: { name: 'Bot de Discord · Eventos', channelKey: 'events, guides, builds ...', template: 'Indicación opcional de enrutado o formato' }, eventsHint: 'Crea integraciones separadas para enviar grupos a distintos canales de Discord.', actions: { create: 'Crear webhook', edit: 'Editar', test: 'Enviar prueba', rotate: 'Rotar secreto', retry: 'Reintentar' }, status: { active: 'Activo', inactive: 'Inactivo', success: 'Entregado', failed: 'Fallido', queued: 'En cola' },
        secret: { oneTime: 'Copia ahora el secreto de firma', hint: 'El secreto completo solo se muestra al crear o rotar.', copy: 'Copiar secreto' }, readOnly: { eyebrow: 'Solo lectura', title: 'Monitor de integraciones', hint: 'Los moderadores pueden revisar endpoints y entregas. Solo los administradores pueden modificarlos.' }, list: { eyebrow: 'Endpoints configurados', title: 'Suscripciones webhook', noChannel: 'Sin clave de canal', events: 'eventos', secret: 'Secreto', lastSuccess: 'Último éxito', lastFailure: 'Último fallo' }, deliveries: { eyebrow: 'Monitor de entregas', title: 'Entregas webhook recientes', allWebhooks: 'Todos los webhooks', allStatuses: 'Todos los estados', empty: 'No hay entregas registradas.', created: 'Creado', webhook: 'Integración', event: 'Evento', resource: 'Recurso', status: 'Estado', attempts: 'Intentos', details: 'Detalles' }, messages: { created: 'Webhook creado.', updated: 'Webhook actualizado.', testSuccess: 'Prueba correcta.', testFailed: 'La prueba falló. Revisa el historial.', rotated: 'Secreto rotado.', deleted: 'Webhook eliminado.', retrySuccess: 'Reintento correcto.', retryFailed: 'El reintento falló.', secretCopied: 'Secreto copiado.' }, errors: { load: 'No se pudieron cargar las integraciones.', save: 'No se pudo guardar el webhook.', test: 'No se pudo enviar la prueba.', rotate: 'No se pudo rotar el secreto.', delete: 'No se pudo eliminar el webhook.', retry: 'No se pudo reintentar la entrega.' },
      },
    },
  },
  pt: {
    admin: {
      tabs: { integrations: 'Integrações' }, audit: { entities: { outbound_webhook: 'Webhook de saída' } },
      webhooks: {
        eyebrow: 'Automação externa', title: 'Webhooks de saída', subtitle: 'Envie eventos assinados ao bot do Discord ou a outro serviço.', loading: 'A carregar integrações ...', empty: 'Nenhum webhook configurado.', confirmDelete: 'Eliminar o webhook “{name}” e o histórico?', summary: { total: 'Configurados', totalHint: 'Todos os endpoints', active: 'Ativos', activeHint: 'Recebem novos eventos', failing: 'Requer atenção', failingHint: 'Última entrega falhou', deliveries: 'Sucesso / falha', deliveriesHint: 'Histórico guardado' }, editor: { eyebrow: 'Configuração do endpoint', createTitle: 'Criar integração', editTitle: 'Editar integração' }, fields: { name: 'Nome', endpoint: 'URL do bot', channelKey: 'Chave do canal', active: 'Integração ativa', template: 'Modelo opcional', events: 'Eventos subscritos' }, placeholders: { name: 'Bot Discord · Eventos', channelKey: 'events, guides, builds ...', template: 'Indicação opcional de encaminhamento ou formato' }, eventsHint: 'Crie integrações separadas para enviar grupos a canais diferentes.', actions: { create: 'Criar webhook', edit: 'Editar', test: 'Enviar teste', rotate: 'Rodar segredo', retry: 'Tentar novamente' }, status: { active: 'Ativo', inactive: 'Inativo', success: 'Entregue', failed: 'Falhou', queued: 'Na fila' }, secret: { oneTime: 'Copie agora o segredo de assinatura', hint: 'O segredo completo só aparece após criação ou rotação.', copy: 'Copiar segredo' }, readOnly: { eyebrow: 'Apenas leitura', title: 'Monitorização das integrações', hint: 'Moderadores podem consultar endpoints e entregas. Só administradores podem alterar.' }, list: { eyebrow: 'Endpoints configurados', title: 'Subscrições webhook', noChannel: 'Sem chave de canal', events: 'eventos', secret: 'Segredo', lastSuccess: 'Último sucesso', lastFailure: 'Última falha' }, deliveries: { eyebrow: 'Monitor de entregas', title: 'Entregas webhook recentes', allWebhooks: 'Todos os webhooks', allStatuses: 'Todos os estados', empty: 'Nenhuma entrega registada.', created: 'Criado', webhook: 'Integração', event: 'Evento', resource: 'Recurso', status: 'Estado', attempts: 'Tentativas', details: 'Detalhes' }, messages: { created: 'Webhook criado.', updated: 'Webhook atualizado.', testSuccess: 'Teste com sucesso.', testFailed: 'O teste falhou. Consulte o histórico.', rotated: 'Segredo rodado.', deleted: 'Webhook eliminado.', retrySuccess: 'Nova tentativa concluída.', retryFailed: 'Nova tentativa falhou.', secretCopied: 'Segredo copiado.' }, errors: { load: 'Não foi possível carregar as integrações.', save: 'Não foi possível guardar o webhook.', test: 'Não foi possível enviar o teste.', rotate: 'Não foi possível rodar o segredo.', delete: 'Não foi possível eliminar o webhook.', retry: 'Não foi possível repetir a entrega.' },
      },
    },
  },
  ru: {
    admin: {
      tabs: { integrations: 'Интеграции' }, audit: { entities: { outbound_webhook: 'Исходящий webhook' } },
      webhooks: {
        eyebrow: 'Внешняя автоматизация', title: 'Исходящие webhooks', subtitle: 'Отправляйте подписанные события Discord-боту или другому сервису.', loading: 'Загрузка интеграций ...', empty: 'Исходящие webhooks ещё не настроены.', confirmDelete: 'Удалить webhook «{name}» и историю доставок?', summary: { total: 'Настроено', totalHint: 'Все конечные точки', active: 'Активно', activeHint: 'Получают новые события', failing: 'Требуют внимания', failingHint: 'Последняя доставка не удалась', deliveries: 'Успех / ошибка', deliveriesHint: 'Сохранённая история' }, editor: { eyebrow: 'Настройка конечной точки', createTitle: 'Создать интеграцию', editTitle: 'Изменить интеграцию' }, fields: { name: 'Название', endpoint: 'URL бота', channelKey: 'Ключ канала', active: 'Интеграция активна', template: 'Необязательный шаблон', events: 'Подписки на события' }, placeholders: { name: 'Discord-бот · События', channelKey: 'events, guides, builds ...', template: 'Подсказка маршрутизации или формата для бота' }, eventsHint: 'Создавайте отдельные интеграции для разных каналов Discord.', actions: { create: 'Создать webhook', edit: 'Изменить', test: 'Отправить тест', rotate: 'Сменить секрет', retry: 'Повторить' }, status: { active: 'Активен', inactive: 'Неактивен', success: 'Доставлено', failed: 'Ошибка', queued: 'В очереди' }, secret: { oneTime: 'Скопируйте секрет подписи сейчас', hint: 'Полный секрет показывается только после создания или смены.', copy: 'Копировать секрет' }, readOnly: { eyebrow: 'Только чтение', title: 'Мониторинг интеграций', hint: 'Модераторы видят точки и доставки. Изменять их могут только администраторы.' }, list: { eyebrow: 'Настроенные точки', title: 'Подписки webhook', noChannel: 'Без ключа канала', events: 'событий', secret: 'Секрет', lastSuccess: 'Последний успех', lastFailure: 'Последняя ошибка' }, deliveries: { eyebrow: 'Монитор доставки', title: 'Последние доставки webhook', allWebhooks: 'Все webhooks', allStatuses: 'Все статусы', empty: 'Доставок пока нет.', created: 'Создано', webhook: 'Интеграция', event: 'Событие', resource: 'Ресурс', status: 'Статус', attempts: 'Попытки', details: 'Детали' }, messages: { created: 'Webhook создан.', updated: 'Webhook обновлён.', testSuccess: 'Тест успешен.', testFailed: 'Тест не удался. Проверьте историю.', rotated: 'Секрет изменён.', deleted: 'Webhook удалён.', retrySuccess: 'Повторная доставка успешна.', retryFailed: 'Повторная доставка не удалась.', secretCopied: 'Секрет скопирован.' }, errors: { load: 'Не удалось загрузить интеграции.', save: 'Не удалось сохранить webhook.', test: 'Не удалось отправить тест.', rotate: 'Не удалось сменить секрет.', delete: 'Не удалось удалить webhook.', retry: 'Не удалось повторить доставку.' },
      },
    },
  },
  cn: {
    admin: {
      tabs: { integrations: '集成' }, audit: { entities: { outbound_webhook: '出站 Webhook' } },
      webhooks: {
        eyebrow: '外部自动化', title: '出站 Webhook', subtitle: '将已签名的项目事件发送到 Discord 机器人或其他集成服务。', loading: '正在加载集成 ...', empty: '尚未配置出站 Webhook。', confirmDelete: '删除 Webhook“{name}”及其投递历史？', summary: { total: '已配置', totalHint: '全部端点', active: '活动', activeHint: '接收新事件', failing: '需要处理', failingHint: '最近投递失败', deliveries: '成功 / 失败', deliveriesHint: '已保存的投递历史' }, editor: { eyebrow: '端点配置', createTitle: '创建集成', editTitle: '编辑集成' }, fields: { name: '名称', endpoint: '机器人端点 URL', channelKey: '频道键', active: '启用集成', template: '可选消息模板', events: '订阅事件' }, placeholders: { name: 'Discord 机器人 · 活动', channelKey: 'events, guides, builds ...', template: '提供给机器人的可选路由或格式提示' }, eventsHint: '不同事件组需要进入不同 Discord 频道时，请创建单独集成。', actions: { create: '创建 Webhook', edit: '编辑', test: '发送测试', rotate: '轮换密钥', retry: '重试' }, status: { active: '活动', inactive: '停用', success: '已投递', failed: '失败', queued: '排队中' }, secret: { oneTime: '立即复制签名密钥', hint: '完整密钥仅在创建或轮换后显示。', copy: '复制密钥' }, readOnly: { eyebrow: '只读访问', title: '集成监控', hint: '版主可以查看端点和投递记录，只有管理员可以修改。' }, list: { eyebrow: '已配置端点', title: 'Webhook 订阅', noChannel: '无频道键', events: '个事件', secret: '密钥', lastSuccess: '最近成功', lastFailure: '最近失败' }, deliveries: { eyebrow: '投递监控', title: '最近 Webhook 投递', allWebhooks: '全部 Webhook', allStatuses: '全部状态', empty: '尚无投递记录。', created: '创建时间', webhook: '集成端点', event: '事件', resource: '资源', status: '状态', attempts: '尝试次数', details: '详情' }, messages: { created: 'Webhook 已创建。', updated: 'Webhook 已更新。', testSuccess: '测试投递成功。', testFailed: '测试投递失败，请查看历史。', rotated: '签名密钥已轮换。', deleted: 'Webhook 已删除。', retrySuccess: '重试投递成功。', retryFailed: '重试投递失败。', secretCopied: '签名密钥已复制。' }, errors: { load: '无法加载集成。', save: '无法保存 Webhook。', test: '无法发送测试。', rotate: '无法轮换密钥。', delete: '无法删除 Webhook。', retry: '无法重试投递。' },
      },
    },
  },
}
