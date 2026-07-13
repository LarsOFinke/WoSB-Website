export const securityAuditDashboardMessages = {
  en: {
    admin: {
      tabs: { audit: 'Audit history' },
      logs: {
        sortDate: 'Sort by date', sortIp: 'Sort by IP', sortStatus: 'Sort by status', sortDuration: 'Sort by duration', sortLevel: 'Sort by level',
        desc: 'Descending', asc: 'Ascending',
      },
      security: {
        title: 'Security monitoring', subtitle: 'Daily request patterns and IP threat scoring from persisted system logs.',
        from: 'From', to: 'To', sort: 'IP sorting', sortThreat: 'Highest threat', sortRequests: 'Most requests', sortRecent: 'Most recent', sortIp: 'IP address', selectedIp: 'Focused IP', allIps: 'All IPs',
        currentThreat: 'Current threat level', requests: 'Requests', uniqueIps: 'Unique IPs', suspicious: 'Suspicious hits', loading: 'Loading security dashboard ...', loadError: 'Security dashboard could not be loaded.',
        byDay: 'Activity by day', byIp: 'IP threat overview', day: 'Day', paths: 'paths', lastSeen: 'Last seen', noIps: 'No IP activity in this period.',
        methodNote: 'Threat scores are monitoring indicators based on errors, 4xx/5xx responses, suspicious probe paths and request patterns. They are not an automatic block list.',
        levels: { low: 'Low', guarded: 'Guarded', elevated: 'Elevated', critical: 'Critical' },
      },
      audit: {
        title: 'Audit history', subtitle: 'Who changed which managed content, when it happened and which fields were touched.',
        loading: 'Loading audit history ...', loadError: 'Audit history could not be loaded.', empty: 'No matching changes found.',
        allEntities: 'All content types', allActions: 'All actions', actorPlaceholder: 'Filter by user', fields: 'Changed fields',
        actions: { create: 'Created', update: 'Updated', delete: 'Deleted' },
        entities: { build: 'Build', forum_thread: 'Forum thread', forum_post: 'Forum post', guide: 'Guide', newcomer_guide: 'Starter guide' },
      },
    },
    builds: { visuals: { selectedShip: 'Selected ship' } },
  },
  de: {
    admin: {
      tabs: { audit: 'Änderungshistorie' },
      logs: {
        sortDate: 'Nach Datum sortieren', sortIp: 'Nach IP sortieren', sortStatus: 'Nach Status sortieren', sortDuration: 'Nach Dauer sortieren', sortLevel: 'Nach Level sortieren',
        desc: 'Absteigend', asc: 'Aufsteigend',
      },
      security: {
        title: 'Security-Monitoring', subtitle: 'Tägliche Request-Muster und IP-Bedrohungsbewertung aus den gespeicherten Systemlogs.',
        from: 'Von', to: 'Bis', sort: 'IP-Sortierung', sortThreat: 'Höchste Bedrohung', sortRequests: 'Meiste Requests', sortRecent: 'Zuletzt aktiv', sortIp: 'IP-Adresse', selectedIp: 'Fokussierte IP', allIps: 'Alle IPs',
        currentThreat: 'Aktuelles Threat-Level', requests: 'Anfragen', uniqueIps: 'Eindeutige IPs', suspicious: 'Verdächtige Treffer', loading: 'Security-Dashboard wird geladen ...', loadError: 'Security-Dashboard konnte nicht geladen werden.',
        byDay: 'Aktivität nach Tagen', byIp: 'IP-Threat-Übersicht', day: 'Tag', paths: 'Pfade', lastSeen: 'Zuletzt gesehen', noIps: 'Keine IP-Aktivität in diesem Zeitraum.',
        methodNote: 'Threat-Scores sind Monitoring-Indikatoren aus Fehlern, 4xx-/5xx-Antworten, verdächtigen Scan-Pfaden und Request-Mustern. Sie sind keine automatische Sperrliste.',
        levels: { low: 'Niedrig', guarded: 'Beobachten', elevated: 'Erhöht', critical: 'Kritisch' },
      },
      audit: {
        title: 'Änderungshistorie', subtitle: 'Wer wann welche verwalteten Inhalte geändert hat und welche Felder betroffen waren.',
        loading: 'Änderungshistorie wird geladen ...', loadError: 'Änderungshistorie konnte nicht geladen werden.', empty: 'Keine passenden Änderungen gefunden.',
        allEntities: 'Alle Inhaltstypen', allActions: 'Alle Aktionen', actorPlaceholder: 'Nach Benutzer filtern', fields: 'Geänderte Felder',
        actions: { create: 'Erstellt', update: 'Geändert', delete: 'Gelöscht' },
        entities: { build: 'Schiffskonfiguration', forum_thread: 'Forum-Thread', forum_post: 'Forum-Beitrag', guide: 'Leitfaden', newcomer_guide: 'Starter-Leitfaden' },
      },
    },
    builds: { visuals: { selectedShip: 'Ausgewähltes Schiff' } },
  },
  fr: {
    admin: {
      tabs: { audit: 'Historique d’audit' },
      logs: { sortDate: 'Trier par date', sortIp: 'Trier par IP', sortStatus: 'Trier par statut', sortDuration: 'Trier par durée', sortLevel: 'Trier par niveau', desc: 'Décroissant', asc: 'Croissant' },
      security: { title: 'Surveillance de sécurité', subtitle: 'Tendances quotidiennes et niveau de menace des IP à partir des journaux.', from: 'Du', to: 'Au', sort: 'Tri des IP', sortThreat: 'Menace la plus élevée', sortRequests: 'Plus de requêtes', sortRecent: 'Plus récent', sortIp: 'Adresse IP', selectedIp: 'IP ciblée', allIps: 'Toutes les IP', currentThreat: 'Niveau de menace actuel', requests: 'Requêtes', uniqueIps: 'IP uniques', suspicious: 'Détections suspectes', loading: 'Chargement du tableau de sécurité ...', loadError: 'Impossible de charger le tableau de sécurité.', byDay: 'Activité par jour', byIp: 'Aperçu des menaces IP', day: 'Jour', paths: 'chemins', lastSeen: 'Dernière activité', noIps: 'Aucune activité IP sur cette période.', methodNote: 'Les scores sont des indicateurs de suivi basés sur les erreurs, réponses 4xx/5xx, chemins de scan et schémas de requêtes. Ils ne bloquent pas automatiquement.', levels: { low: 'Faible', guarded: 'Surveillé', elevated: 'Élevé', critical: 'Critique' } },
      audit: { title: 'Historique d’audit', subtitle: 'Qui a modifié quel contenu, quand et quels champs ont changé.', loading: 'Chargement de l’historique ...', loadError: 'Impossible de charger l’historique.', empty: 'Aucune modification correspondante.', allEntities: 'Tous les contenus', allActions: 'Toutes les actions', actorPlaceholder: 'Filtrer par utilisateur', fields: 'Champs modifiés', actions: { create: 'Créé', update: 'Modifié', delete: 'Supprimé' }, entities: { build: 'Configuration', forum_thread: 'Sujet du forum', forum_post: 'Message du forum', guide: 'Manuel', newcomer_guide: 'Guide de démarrage' } },
    },
    builds: { visuals: { selectedShip: 'Navire sélectionné' } },
  },
  es: {
    admin: {
      tabs: { audit: 'Historial de auditoría' },
      logs: { sortDate: 'Ordenar por fecha', sortIp: 'Ordenar por IP', sortStatus: 'Ordenar por estado', sortDuration: 'Ordenar por duración', sortLevel: 'Ordenar por nivel', desc: 'Descendente', asc: 'Ascendente' },
      security: { title: 'Monitorización de seguridad', subtitle: 'Patrones diarios y nivel de amenaza de IP según los registros guardados.', from: 'Desde', to: 'Hasta', sort: 'Orden de IP', sortThreat: 'Mayor amenaza', sortRequests: 'Más solicitudes', sortRecent: 'Más reciente', sortIp: 'Dirección IP', selectedIp: 'IP enfocada', allIps: 'Todas las IP', currentThreat: 'Nivel de amenaza actual', requests: 'Solicitudes', uniqueIps: 'IP únicas', suspicious: 'Detecciones sospechosas', loading: 'Cargando panel de seguridad ...', loadError: 'No se pudo cargar el panel de seguridad.', byDay: 'Actividad por día', byIp: 'Resumen de amenaza por IP', day: 'Día', paths: 'rutas', lastSeen: 'Última actividad', noIps: 'Sin actividad IP en este periodo.', methodNote: 'Las puntuaciones son indicadores basados en errores, respuestas 4xx/5xx, rutas de escaneo y patrones de solicitudes. No bloquean automáticamente.', levels: { low: 'Bajo', guarded: 'Vigilado', elevated: 'Elevado', critical: 'Crítico' } },
      audit: { title: 'Historial de auditoría', subtitle: 'Quién cambió qué contenido, cuándo y qué campos fueron afectados.', loading: 'Cargando historial ...', loadError: 'No se pudo cargar el historial.', empty: 'No hay cambios coincidentes.', allEntities: 'Todos los contenidos', allActions: 'Todas las acciones', actorPlaceholder: 'Filtrar por usuario', fields: 'Campos cambiados', actions: { create: 'Creado', update: 'Actualizado', delete: 'Eliminado' }, entities: { build: 'Configuración', forum_thread: 'Tema del foro', forum_post: 'Mensaje del foro', guide: 'Guía', newcomer_guide: 'Guía inicial' } },
    },
    builds: { visuals: { selectedShip: 'Barco seleccionado' } },
  },
  pt: {
    admin: {
      tabs: { audit: 'Histórico de auditoria' },
      logs: { sortDate: 'Ordenar por data', sortIp: 'Ordenar por IP', sortStatus: 'Ordenar por estado', sortDuration: 'Ordenar por duração', sortLevel: 'Ordenar por nível', desc: 'Descendente', asc: 'Ascendente' },
      security: { title: 'Monitorização de segurança', subtitle: 'Padrões diários e nível de ameaça de IP com base nos logs guardados.', from: 'De', to: 'Até', sort: 'Ordenação de IP', sortThreat: 'Maior ameaça', sortRequests: 'Mais pedidos', sortRecent: 'Mais recente', sortIp: 'Endereço IP', selectedIp: 'IP em foco', allIps: 'Todos os IPs', currentThreat: 'Nível de ameaça atual', requests: 'Pedidos', uniqueIps: 'IPs únicos', suspicious: 'Ocorrências suspeitas', loading: 'A carregar painel de segurança ...', loadError: 'Não foi possível carregar o painel de segurança.', byDay: 'Atividade por dia', byIp: 'Visão de ameaça por IP', day: 'Dia', paths: 'caminhos', lastSeen: 'Última atividade', noIps: 'Sem atividade IP neste período.', methodNote: 'As pontuações são indicadores baseados em erros, respostas 4xx/5xx, caminhos de scan e padrões de pedidos. Não bloqueiam automaticamente.', levels: { low: 'Baixo', guarded: 'Vigiado', elevated: 'Elevado', critical: 'Crítico' } },
      audit: { title: 'Histórico de auditoria', subtitle: 'Quem alterou que conteúdo, quando e quais campos foram afetados.', loading: 'A carregar histórico ...', loadError: 'Não foi possível carregar o histórico.', empty: 'Nenhuma alteração correspondente.', allEntities: 'Todos os conteúdos', allActions: 'Todas as ações', actorPlaceholder: 'Filtrar por utilizador', fields: 'Campos alterados', actions: { create: 'Criado', update: 'Atualizado', delete: 'Eliminado' }, entities: { build: 'Configuração', forum_thread: 'Tópico do fórum', forum_post: 'Mensagem do fórum', guide: 'Guia', newcomer_guide: 'Guia inicial' } },
    },
    builds: { visuals: { selectedShip: 'Navio selecionado' } },
  },
  ru: {
    admin: {
      tabs: { audit: 'История изменений' },
      logs: { sortDate: 'Сортировать по дате', sortIp: 'Сортировать по IP', sortStatus: 'Сортировать по статусу', sortDuration: 'Сортировать по длительности', sortLevel: 'Сортировать по уровню', desc: 'По убыванию', asc: 'По возрастанию' },
      security: { title: 'Мониторинг безопасности', subtitle: 'Дневные шаблоны запросов и оценка угроз IP по сохранённым логам.', from: 'С', to: 'По', sort: 'Сортировка IP', sortThreat: 'Наивысшая угроза', sortRequests: 'Больше запросов', sortRecent: 'Последняя активность', sortIp: 'IP-адрес', selectedIp: 'Выбранный IP', allIps: 'Все IP', currentThreat: 'Текущий уровень угрозы', requests: 'Запросы', uniqueIps: 'Уникальные IP', suspicious: 'Подозрительные события', loading: 'Загрузка панели безопасности ...', loadError: 'Не удалось загрузить панель безопасности.', byDay: 'Активность по дням', byIp: 'Обзор угроз по IP', day: 'День', paths: 'пути', lastSeen: 'Последняя активность', noIps: 'Нет IP-активности за этот период.', methodNote: 'Оценки — индикаторы мониторинга по ошибкам, ответам 4xx/5xx, путям сканирования и шаблонам запросов. Они не блокируют IP автоматически.', levels: { low: 'Низкий', guarded: 'Наблюдение', elevated: 'Повышенный', critical: 'Критический' } },
      audit: { title: 'История изменений', subtitle: 'Кто, когда и какие управляемые материалы менял, а также затронутые поля.', loading: 'Загрузка истории ...', loadError: 'Не удалось загрузить историю.', empty: 'Подходящих изменений нет.', allEntities: 'Все типы контента', allActions: 'Все действия', actorPlaceholder: 'Фильтр по пользователю', fields: 'Изменённые поля', actions: { create: 'Создано', update: 'Изменено', delete: 'Удалено' }, entities: { build: 'Билд', forum_thread: 'Тема форума', forum_post: 'Сообщение форума', guide: 'Руководство', newcomer_guide: 'Стартовое руководство' } },
    },
    builds: { visuals: { selectedShip: 'Выбранный корабль' } },
  },
  cn: {
    admin: {
      tabs: { audit: '审计历史' },
      logs: { sortDate: '按日期排序', sortIp: '按 IP 排序', sortStatus: '按状态排序', sortDuration: '按耗时排序', sortLevel: '按级别排序', desc: '降序', asc: '升序' },
      security: { title: '安全监控', subtitle: '基于已保存系统日志的每日请求趋势和 IP 威胁评分。', from: '开始', to: '结束', sort: 'IP 排序', sortThreat: '最高威胁', sortRequests: '最多请求', sortRecent: '最近活动', sortIp: 'IP 地址', selectedIp: '聚焦 IP', allIps: '全部 IP', currentThreat: '当前威胁等级', requests: '请求', uniqueIps: '唯一 IP', suspicious: '可疑命中', loading: '正在加载安全面板 ...', loadError: '无法加载安全面板。', byDay: '按天活动', byIp: 'IP 威胁概览', day: '日期', paths: '路径', lastSeen: '最后出现', noIps: '此期间没有 IP 活动。', methodNote: '威胁分数是根据错误、4xx/5xx、可疑扫描路径和请求模式得出的监控指标，不会自动封禁。', levels: { low: '低', guarded: '关注', elevated: '升高', critical: '严重' } },
      audit: { title: '审计历史', subtitle: '查看谁在何时修改了哪些受管内容及涉及的字段。', loading: '正在加载审计历史 ...', loadError: '无法加载审计历史。', empty: '没有匹配的变更。', allEntities: '所有内容类型', allActions: '所有操作', actorPlaceholder: '按用户筛选', fields: '变更字段', actions: { create: '已创建', update: '已更新', delete: '已删除' }, entities: { build: '配置', forum_thread: '论坛主题', forum_post: '论坛帖子', guide: '指南', newcomer_guide: '新手指南' } },
    },
    builds: { visuals: { selectedShip: '已选择船只' } },
  },
}
