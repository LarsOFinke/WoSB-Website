export const ipBlockManagementMessages = {
  en: {
    admin: {
      tabs: { ipBlocks: 'IP blocks' },
      security: { blockSelectedIp: 'Block this IP' },
      audit: { entities: { ip_block: 'IP block' } },
      ipBlocks: {
        title: 'IP block management', subtitle: 'Block or release exact client IP addresses and keep a staff-visible history.', createEyebrow: 'Access control', createTitle: 'Block an IP address', exactOnly: 'Exact IP only', ipAddress: 'IP address', ipPlaceholder: 'e.g. 203.0.113.42 or 2001:db8::42', reason: 'Reason', reasonPlaceholder: 'Short security reason', notes: 'Internal notes', notesPlaceholder: 'Optional context for other staff members', duration: 'Duration', expiresAt: 'Expires at', safetyNote: 'Your current staff-session IP, loopback and multicast addresses cannot be blocked.', readOnlyEyebrow: 'Read-only access', readOnlyTitle: 'Monitoring for moderators', readOnlyHint: 'Moderators can review the blocklist and open matching logs. Only administrators can create or release IP blocks.', blockAction: 'Block IP', saving: 'Saving ...', created: 'IP address blocked.', createError: 'The IP address could not be blocked.', customExpiryRequired: 'Choose a custom expiration date and time.', listEyebrow: 'Blocklist', listTitle: 'Managed IP addresses', searchPlaceholder: 'Search IP, reason or staff member', loading: 'Loading IP blocks ...', loadError: 'IP blocks could not be loaded.', empty: 'No matching IP blocks found.', unblockAction: 'Unblock', viewLogs: 'View logs', confirmUnblock: 'Confirm unblock', unblockReasonPlaceholder: 'Optional reason for unblocking', unblocked: 'IP address unblocked.', unblockError: 'The IP address could not be unblocked.', createdBy: 'Blocked by {user} on {date}', expires: 'Expires {date}', unblockedBy: 'Unblocked by {user} on {date}',
        summary: { active: 'Active blocks', activeHint: 'Currently enforced', permanent: 'Permanent', permanentHint: 'No automatic expiry', temporary: 'Temporary', temporaryHint: 'Expires automatically', history: 'History', historyHint: 'Expired or released' },
        durations: { permanent: 'Permanent', oneHour: '1 hour', oneDay: '24 hours', sevenDays: '7 days', thirtyDays: '30 days', custom: 'Custom' },
        filters: { active: 'Active', expired: 'Expired', unblocked: 'Unblocked', all: 'All entries' },
        status: { permanent: 'Permanent', temporary: 'Temporary', expired: 'Expired', unblocked: 'Unblocked' },
      },
    },
  },
  de: {
    admin: {
      tabs: { ipBlocks: 'IP-Sperren' },
      security: { blockSelectedIp: 'Diese IP sperren' },
      audit: { entities: { ip_block: 'IP-Sperre' } },
      ipBlocks: {
        title: 'IP-Sperrverwaltung', subtitle: 'Exakte Client-IP-Adressen sperren oder freigeben und die Historie für Staff-Mitglieder nachvollziehbar halten.', createEyebrow: 'Zugriffskontrolle', createTitle: 'IP-Adresse sperren', exactOnly: 'Nur exakte IP', ipAddress: 'IP-Adresse', ipPlaceholder: 'z. B. 203.0.113.42 oder 2001:db8::42', reason: 'Grund', reasonPlaceholder: 'Kurzer Sicherheitsgrund', notes: 'Interne Notizen', notesPlaceholder: 'Optionaler Kontext für andere Staff-Mitglieder', duration: 'Dauer', expiresAt: 'Läuft ab am', safetyNote: 'Die IP der aktuellen Staff-Sitzung sowie Loopback- und Multicast-Adressen können nicht gesperrt werden.', readOnlyEyebrow: 'Nur-Lese-Zugriff', readOnlyTitle: 'Monitoring für Moderatoren', readOnlyHint: 'Moderatoren können die Sperrliste prüfen und passende Logs öffnen. Nur Administratoren dürfen IP-Sperren erstellen oder aufheben.', blockAction: 'IP sperren', saving: 'Wird gespeichert ...', created: 'IP-Adresse wurde gesperrt.', createError: 'Die IP-Adresse konnte nicht gesperrt werden.', customExpiryRequired: 'Bitte ein individuelles Ablaufdatum wählen.', listEyebrow: 'Sperrliste', listTitle: 'Verwaltete IP-Adressen', searchPlaceholder: 'IP, Grund oder Staff-Mitglied suchen', loading: 'IP-Sperren werden geladen ...', loadError: 'IP-Sperren konnten nicht geladen werden.', empty: 'Keine passenden IP-Sperren gefunden.', unblockAction: 'Entsperren', viewLogs: 'Logs anzeigen', confirmUnblock: 'Entsperrung bestätigen', unblockReasonPlaceholder: 'Optionaler Grund für die Entsperrung', unblocked: 'IP-Adresse wurde entsperrt.', unblockError: 'Die IP-Adresse konnte nicht entsperrt werden.', createdBy: 'Gesperrt von {user} am {date}', expires: 'Läuft ab am {date}', unblockedBy: 'Entsperrt von {user} am {date}',
        summary: { active: 'Aktive Sperren', activeHint: 'Aktuell durchgesetzt', permanent: 'Dauerhaft', permanentHint: 'Ohne automatisches Ende', temporary: 'Temporär', temporaryHint: 'Läuft automatisch ab', history: 'Historie', historyHint: 'Abgelaufen oder freigegeben' },
        durations: { permanent: 'Dauerhaft', oneHour: '1 Stunde', oneDay: '24 Stunden', sevenDays: '7 Tage', thirtyDays: '30 Tage', custom: 'Individuell' },
        filters: { active: 'Aktiv', expired: 'Abgelaufen', unblocked: 'Entsperrt', all: 'Alle Einträge' },
        status: { permanent: 'Dauerhaft', temporary: 'Temporär', expired: 'Abgelaufen', unblocked: 'Entsperrt' },
      },
    },
  },
  fr: {
    admin: {
      tabs: { ipBlocks: 'Blocages IP' },
      security: { blockSelectedIp: 'Bloquer cette IP' },
      audit: { entities: { ip_block: 'Blocage IP' } },
      ipBlocks: {
        title: 'Gestion des blocages IP', subtitle: 'Bloquez ou libérez des adresses IP clientes exactes avec un historique visible par le staff.', createEyebrow: 'Contrôle d’accès', createTitle: 'Bloquer une adresse IP', exactOnly: 'IP exacte uniquement', ipAddress: 'Adresse IP', ipPlaceholder: 'ex. 203.0.113.42 ou 2001:db8::42', reason: 'Motif', reasonPlaceholder: 'Motif de sécurité bref', notes: 'Notes internes', notesPlaceholder: 'Contexte facultatif pour le staff', duration: 'Durée', expiresAt: 'Expiration', safetyNote: 'L’IP de votre session staff, les adresses de bouclage et multicast ne peuvent pas être bloquées.', readOnlyEyebrow: 'Accès en lecture seule', readOnlyTitle: 'Suivi pour les modérateurs', readOnlyHint: 'Les modérateurs peuvent consulter les blocages et ouvrir les journaux associés. Seuls les administrateurs peuvent bloquer ou débloquer une IP.', blockAction: 'Bloquer l’IP', saving: 'Enregistrement ...', created: 'Adresse IP bloquée.', createError: 'Impossible de bloquer l’adresse IP.', customExpiryRequired: 'Choisissez une date et une heure d’expiration.', listEyebrow: 'Liste de blocage', listTitle: 'Adresses IP gérées', searchPlaceholder: 'Rechercher IP, motif ou membre du staff', loading: 'Chargement des blocages IP ...', loadError: 'Impossible de charger les blocages IP.', empty: 'Aucun blocage IP correspondant.', unblockAction: 'Débloquer', viewLogs: 'Voir les journaux', confirmUnblock: 'Confirmer le déblocage', unblockReasonPlaceholder: 'Motif facultatif du déblocage', unblocked: 'Adresse IP débloquée.', unblockError: 'Impossible de débloquer l’adresse IP.', createdBy: 'Bloquée par {user} le {date}', expires: 'Expire le {date}', unblockedBy: 'Débloquée par {user} le {date}',
        summary: { active: 'Blocages actifs', activeHint: 'Appliqués maintenant', permanent: 'Permanents', permanentHint: 'Sans expiration', temporary: 'Temporaires', temporaryHint: 'Expiration automatique', history: 'Historique', historyHint: 'Expirés ou libérés' },
        durations: { permanent: 'Sans limite', oneHour: '1 heure', oneDay: '24 heures', sevenDays: '7 jours', thirtyDays: '30 jours', custom: 'Personnalisé' },
        filters: { active: 'Actifs', expired: 'Expirés', unblocked: 'Débloqués', all: 'Toutes les entrées' },
        status: { permanent: 'Sans limite', temporary: 'Temporaire', expired: 'Expiré', unblocked: 'Débloqué' },
      },
    },
  },
  es: {
    admin: {
      tabs: { ipBlocks: 'Bloqueos IP' },
      security: { blockSelectedIp: 'Bloquear esta IP' },
      audit: { entities: { ip_block: 'Bloqueo IP' } },
      ipBlocks: {
        title: 'Gestión de bloqueos IP', subtitle: 'Bloquea o libera direcciones IP exactas y conserva un historial visible para el staff.', createEyebrow: 'Control de acceso', createTitle: 'Bloquear una dirección IP', exactOnly: 'Solo IP exacta', ipAddress: 'Dirección IP', ipPlaceholder: 'p. ej. 203.0.113.42 o 2001:db8::42', reason: 'Motivo', reasonPlaceholder: 'Motivo de seguridad breve', notes: 'Notas internas', notesPlaceholder: 'Contexto opcional para el staff', duration: 'Duración', expiresAt: 'Caduca el', safetyNote: 'No se puede bloquear la IP de la sesión actual ni direcciones loopback o multicast.', readOnlyEyebrow: 'Acceso de solo lectura', readOnlyTitle: 'Supervisión para moderadores', readOnlyHint: 'Los moderadores pueden revisar la lista y abrir logs relacionados. Solo los administradores pueden bloquear o desbloquear IP.', blockAction: 'Bloquear IP', saving: 'Guardando ...', created: 'Dirección IP bloqueada.', createError: 'No se pudo bloquear la dirección IP.', customExpiryRequired: 'Elige una fecha y hora de caducidad.', listEyebrow: 'Lista de bloqueos', listTitle: 'Direcciones IP gestionadas', searchPlaceholder: 'Buscar IP, motivo o miembro del staff', loading: 'Cargando bloqueos IP ...', loadError: 'No se pudieron cargar los bloqueos IP.', empty: 'No hay bloqueos IP coincidentes.', unblockAction: 'Desbloquear', viewLogs: 'Ver logs', confirmUnblock: 'Confirmar desbloqueo', unblockReasonPlaceholder: 'Motivo opcional del desbloqueo', unblocked: 'Dirección IP desbloqueada.', unblockError: 'No se pudo desbloquear la dirección IP.', createdBy: 'Bloqueada por {user} el {date}', expires: 'Caduca el {date}', unblockedBy: 'Desbloqueada por {user} el {date}',
        summary: { active: 'Bloqueos activos', activeHint: 'Aplicados actualmente', permanent: 'Permanentes', permanentHint: 'Sin caducidad', temporary: 'Temporales', temporaryHint: 'Caducidad automática', history: 'Historial', historyHint: 'Caducados o liberados' },
        durations: { permanent: 'Permanente', oneHour: '1 hora', oneDay: '24 horas', sevenDays: '7 días', thirtyDays: '30 días', custom: 'Personalizado' },
        filters: { active: 'Activos', expired: 'Caducados', unblocked: 'Desbloqueados', all: 'Todas las entradas' },
        status: { permanent: 'Permanente', temporary: 'Temporal', expired: 'Caducado', unblocked: 'Desbloqueado' },
      },
    },
  },
  pt: {
    admin: {
      tabs: { ipBlocks: 'Bloqueios de IP' },
      security: { blockSelectedIp: 'Bloquear este IP' },
      audit: { entities: { ip_block: 'Bloqueio de IP' } },
      ipBlocks: {
        title: 'Gestão de bloqueios de IP', subtitle: 'Bloqueie ou liberte endereços IP exatos e mantenha um histórico visível para a equipa.', createEyebrow: 'Controlo de acesso', createTitle: 'Bloquear endereço IP', exactOnly: 'Apenas IP exato', ipAddress: 'Endereço IP', ipPlaceholder: 'ex. 203.0.113.42 ou 2001:db8::42', reason: 'Motivo', reasonPlaceholder: 'Motivo de segurança breve', notes: 'Notas internas', notesPlaceholder: 'Contexto opcional para a equipa', duration: 'Duração', expiresAt: 'Expira em', safetyNote: 'O IP da sessão atual, endereços loopback e multicast não podem ser bloqueados.', readOnlyEyebrow: 'Acesso só de leitura', readOnlyTitle: 'Monitorização para moderadores', readOnlyHint: 'Moderadores podem consultar a lista e abrir logs relacionados. Só administradores podem bloquear ou desbloquear IPs.', blockAction: 'Bloquear IP', saving: 'A guardar ...', created: 'Endereço IP bloqueado.', createError: 'Não foi possível bloquear o endereço IP.', customExpiryRequired: 'Escolha uma data e hora de expiração.', listEyebrow: 'Lista de bloqueio', listTitle: 'Endereços IP geridos', searchPlaceholder: 'Pesquisar IP, motivo ou membro da equipa', loading: 'A carregar bloqueios de IP ...', loadError: 'Não foi possível carregar os bloqueios de IP.', empty: 'Nenhum bloqueio de IP encontrado.', unblockAction: 'Desbloquear', viewLogs: 'Ver logs', confirmUnblock: 'Confirmar desbloqueio', unblockReasonPlaceholder: 'Motivo opcional do desbloqueio', unblocked: 'Endereço IP desbloqueado.', unblockError: 'Não foi possível desbloquear o endereço IP.', createdBy: 'Bloqueado por {user} em {date}', expires: 'Expira em {date}', unblockedBy: 'Desbloqueado por {user} em {date}',
        summary: { active: 'Bloqueios ativos', activeHint: 'Aplicados agora', permanent: 'Permanentes', permanentHint: 'Sem expiração', temporary: 'Temporários', temporaryHint: 'Expiração automática', history: 'Histórico', historyHint: 'Expirados ou libertados' },
        durations: { permanent: 'Permanente', oneHour: '1 hora', oneDay: '24 horas', sevenDays: '7 dias', thirtyDays: '30 dias', custom: 'Personalizado' },
        filters: { active: 'Ativos', expired: 'Expirados', unblocked: 'Desbloqueados', all: 'Todas as entradas' },
        status: { permanent: 'Permanente', temporary: 'Temporário', expired: 'Expirado', unblocked: 'Desbloqueado' },
      },
    },
  },
  ru: {
    admin: {
      tabs: { ipBlocks: 'Блокировки IP' },
      security: { blockSelectedIp: 'Заблокировать IP' },
      audit: { entities: { ip_block: 'Блокировка IP' } },
      ipBlocks: {
        title: 'Управление блокировками IP', subtitle: 'Блокируйте и освобождайте точные IP-адреса с историей для сотрудников.', createEyebrow: 'Контроль доступа', createTitle: 'Заблокировать IP-адрес', exactOnly: 'Только точный IP', ipAddress: 'IP-адрес', ipPlaceholder: 'например 203.0.113.42 или 2001:db8::42', reason: 'Причина', reasonPlaceholder: 'Краткая причина безопасности', notes: 'Внутренние заметки', notesPlaceholder: 'Необязательный контекст для сотрудников', duration: 'Срок', expiresAt: 'Истекает', safetyNote: 'Нельзя блокировать IP текущей staff-сессии, loopback и multicast-адреса.', readOnlyEyebrow: 'Только чтение', readOnlyTitle: 'Мониторинг для модераторов', readOnlyHint: 'Модераторы могут просматривать список и открывать связанные логи. Создавать и снимать блокировки могут только администраторы.', blockAction: 'Заблокировать IP', saving: 'Сохранение ...', created: 'IP-адрес заблокирован.', createError: 'Не удалось заблокировать IP-адрес.', customExpiryRequired: 'Выберите дату и время окончания.', listEyebrow: 'Список блокировок', listTitle: 'Управляемые IP-адреса', searchPlaceholder: 'Поиск IP, причины или сотрудника', loading: 'Загрузка блокировок IP ...', loadError: 'Не удалось загрузить блокировки IP.', empty: 'Подходящие блокировки IP не найдены.', unblockAction: 'Разблокировать', viewLogs: 'Открыть логи', confirmUnblock: 'Подтвердить разблокировку', unblockReasonPlaceholder: 'Необязательная причина разблокировки', unblocked: 'IP-адрес разблокирован.', unblockError: 'Не удалось разблокировать IP-адрес.', createdBy: 'Заблокировано {user}, {date}', expires: 'Истекает {date}', unblockedBy: 'Разблокировано {user}, {date}',
        summary: { active: 'Активные', activeHint: 'Применяются сейчас', permanent: 'Постоянные', permanentHint: 'Без срока', temporary: 'Временные', temporaryHint: 'Автоматически истекают', history: 'История', historyHint: 'Истекшие или снятые' },
        durations: { permanent: 'Постоянно', oneHour: '1 час', oneDay: '24 часа', sevenDays: '7 дней', thirtyDays: '30 дней', custom: 'Свой срок' },
        filters: { active: 'Активные', expired: 'Истекшие', unblocked: 'Снятые', all: 'Все записи' },
        status: { permanent: 'Постоянно', temporary: 'Временно', expired: 'Истекло', unblocked: 'Снято' },
      },
    },
  },
  cn: {
    admin: {
      tabs: { ipBlocks: 'IP 封禁' },
      security: { blockSelectedIp: '封禁此 IP' },
      audit: { entities: { ip_block: 'IP 封禁' } },
      ipBlocks: {
        title: 'IP 封禁管理', subtitle: '封禁或解除精确客户端 IP，并保留员工可见的操作历史。', createEyebrow: '访问控制', createTitle: '封禁 IP 地址', exactOnly: '仅精确 IP', ipAddress: 'IP 地址', ipPlaceholder: '例如 203.0.113.42 或 2001:db8::42', reason: '原因', reasonPlaceholder: '简短安全原因', notes: '内部备注', notesPlaceholder: '供其他员工参考的可选说明', duration: '期限', expiresAt: '到期时间', safetyNote: '不能封禁当前员工会话 IP、回环地址或组播地址。', readOnlyEyebrow: '只读访问', readOnlyTitle: '版主监控视图', readOnlyHint: '版主可以查看封禁列表和相关日志。只有管理员可以创建或解除 IP 封禁。', blockAction: '封禁 IP', saving: '正在保存 ...', created: 'IP 地址已封禁。', createError: '无法封禁该 IP 地址。', customExpiryRequired: '请选择自定义到期日期和时间。', listEyebrow: '封禁列表', listTitle: '已管理的 IP 地址', searchPlaceholder: '搜索 IP、原因或员工', loading: '正在加载 IP 封禁 ...', loadError: '无法加载 IP 封禁。', empty: '没有匹配的 IP 封禁。', unblockAction: '解除封禁', viewLogs: '查看日志', confirmUnblock: '确认解除', unblockReasonPlaceholder: '可选的解除原因', unblocked: 'IP 地址已解除封禁。', unblockError: '无法解除该 IP 地址。', createdBy: '由 {user} 于 {date} 封禁', expires: '于 {date} 到期', unblockedBy: '由 {user} 于 {date} 解除',
        summary: { active: '活动封禁', activeHint: '当前生效', permanent: '永久', permanentHint: '不会自动到期', temporary: '临时', temporaryHint: '自动到期', history: '历史', historyHint: '已到期或已解除' },
        durations: { permanent: '永久', oneHour: '1 小时', oneDay: '24 小时', sevenDays: '7 天', thirtyDays: '30 天', custom: '自定义' },
        filters: { active: '活动', expired: '已到期', unblocked: '已解除', all: '全部记录' },
        status: { permanent: '永久', temporary: '临时', expired: '已到期', unblocked: '已解除' },
      },
    },
  },
}
