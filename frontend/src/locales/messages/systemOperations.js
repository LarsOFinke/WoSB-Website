export const systemOperationsMessages = {
  en: {
    admin: {
      system: {
        monitoringTitle: 'Uptime monitoring',
        monitoringText: 'Open Uptime Kuma through the dedicated HTTPS gateway. Port 8443 accepts HTTPS only.',
        openMonitoring: 'Open Uptime Kuma',
        httpsHint: 'Always use https:// on port 8443.',
        updateTitle: 'Server update',
        updateText: 'Pull the latest fast-forward release, create a backup, rebuild the application, run migrations and verify readiness.',
        updateButton: 'Update server',
        migrateButton: 'Update + migrate',
        migrateSeedButton: 'Update + migrate + seed',
        migrateConfirm: 'This creates a database backup and runs all migrations without seeding master data. Continue?',
        migrateSeedConfirm: 'This creates a database backup, runs all migrations and the idempotent seed. Continue?',
        updateRunning: 'Update running ...',
        refresh: 'Refresh status',
        statusLabel: 'Update state',
        operation: 'Operation',
        requestedBy: 'Requested by',
        startedAt: 'Started',
        finishedAt: 'Finished',
        commit: 'Revision',
        requestAccepted: 'The update request was accepted by the host runner.',
        migrateRequestAccepted: 'The update with migrations was accepted by the host runner.',
        migrateSeedRequestAccepted: 'The update with migrations and seed was accepted by the host runner.',
        requestError: 'The server update could not be requested.',
        loadError: 'The update status could not be loaded.',
        logTitle: 'Update log',
        logEmpty: 'No update log is available yet.',
        adminOnly: 'Only administrators can start an update.',
        operations: { update: 'Standard update', update_migrate: 'Update + migrations', update_migrate_seed: 'Update + migrations + seed' },
        states: { idle: 'Idle', queued: 'Queued', running: 'Running', succeeded: 'Succeeded', failed: 'Failed' },
      },
      logs: { refresh: 'Refresh logs' },
    },
  },
  de: {
    admin: {
      system: {
        monitoringTitle: 'Uptime-Monitoring',
        monitoringText: 'Uptime Kuma über das separate HTTPS-Gateway öffnen. Port 8443 akzeptiert ausschließlich HTTPS.',
        openMonitoring: 'Uptime Kuma öffnen',
        httpsHint: 'Auf Port 8443 immer https:// verwenden.',
        updateTitle: 'Server-Update',
        updateText: 'Neuestes Fast-Forward-Release laden, Backup erstellen, Anwendung neu bauen, Migrationen ausführen und Bereitschaft prüfen.',
        updateButton: 'Update Server',
        migrateButton: 'Update + Migration',
        migrateSeedButton: 'Update + Migration + Seed',
        migrateConfirm: 'Dabei wird ein Datenbank-Backup erstellt und anschließend werden alle Migrationen ohne Seed ausgeführt. Fortfahren?',
        migrateSeedConfirm: 'Dabei wird ein Datenbank-Backup erstellt, anschließend werden alle Migrationen und der idempotente Seed ausgeführt. Fortfahren?',
        updateRunning: 'Update läuft ...',
        refresh: 'Status aktualisieren',
        statusLabel: 'Update-Status',
        operation: 'Aktion',
        requestedBy: 'Angefordert von',
        startedAt: 'Gestartet',
        finishedAt: 'Beendet',
        commit: 'Versionsstand',
        requestAccepted: 'Die Update-Anfrage wurde vom Host-Runner angenommen.',
        migrateRequestAccepted: 'Das Update mit Migrationen wurde vom Host-Runner angenommen.',
        migrateSeedRequestAccepted: 'Das Update mit Migrationen und Seed wurde vom Host-Runner angenommen.',
        requestError: 'Das Server-Update konnte nicht angefordert werden.',
        loadError: 'Der Update-Status konnte nicht geladen werden.',
        logTitle: 'Update-Protokoll',
        logEmpty: 'Noch kein Update-Protokoll vorhanden.',
        adminOnly: 'Nur Administratoren können ein Update starten.',
        operations: { update: 'Standard-Update', update_migrate: 'Update + Migrationen', update_migrate_seed: 'Update + Migrationen + Seed' },
        states: { idle: 'Bereit', queued: 'Eingereiht', running: 'Läuft', succeeded: 'Erfolgreich', failed: 'Fehlgeschlagen' },
      },
      logs: { refresh: 'Logs aktualisieren' },
    },
  },
  fr: {
    admin: {
      system: {
        monitoringTitle: 'Surveillance Uptime', monitoringText: 'Ouvrez Uptime Kuma via la passerelle HTTPS dédiée. Le port 8443 accepte uniquement HTTPS.', openMonitoring: 'Ouvrir Uptime Kuma', httpsHint: 'Utilisez toujours https:// sur le port 8443.', updateTitle: 'Mise à jour du serveur', updateText: 'Récupère la dernière version fast-forward, crée une sauvegarde, reconstruit l’application, lance les migrations et vérifie le service.', updateButton: 'Mettre à jour le serveur', migrateButton: 'Mise à jour + migrations', migrateSeedButton: 'Mise à jour + migrations + seed', migrateConfirm: 'Une sauvegarde de la base sera créée, puis toutes les migrations seront exécutées sans lancer le seed. Continuer ?', migrateSeedConfirm: 'Une sauvegarde de la base sera créée, puis toutes les migrations et le seed idempotent seront exécutés. Continuer ?', updateRunning: 'Mise à jour en cours ...', refresh: 'Actualiser le statut', statusLabel: 'État de mise à jour', operation: 'Opération', requestedBy: 'Demandé par', startedAt: 'Démarré', finishedAt: 'Terminé', commit: 'Révision', requestAccepted: 'La demande a été acceptée par le runner hôte.', migrateRequestAccepted: 'La mise à jour avec migrations a été acceptée par le runner hôte.', migrateSeedRequestAccepted: 'La mise à jour avec migrations et seed a été acceptée par le runner hôte.', requestError: 'Impossible de demander la mise à jour.', loadError: 'Impossible de charger le statut.', logTitle: 'Journal de mise à jour', logEmpty: 'Aucun journal de mise à jour disponible.', adminOnly: 'Seuls les administrateurs peuvent lancer une mise à jour.', operations: { update: 'Mise à jour standard', update_migrate: 'Mise à jour + migrations', update_migrate_seed: 'Mise à jour + migrations + seed' }, states: { idle: 'Inactif', queued: 'En attente', running: 'En cours', succeeded: 'Réussi', failed: 'Échoué' },
      }, logs: { refresh: 'Actualiser les journaux' },
    },
  },
  es: {
    admin: {
      system: {
        monitoringTitle: 'Monitorización Uptime', monitoringText: 'Abre Uptime Kuma mediante la pasarela HTTPS dedicada. El puerto 8443 solo acepta HTTPS.', openMonitoring: 'Abrir Uptime Kuma', httpsHint: 'Usa siempre https:// en el puerto 8443.', updateTitle: 'Actualización del servidor', updateText: 'Descarga la última versión fast-forward, crea una copia, reconstruye la aplicación, ejecuta migraciones y verifica el servicio.', updateButton: 'Actualizar servidor', migrateButton: 'Actualizar + migrar', migrateSeedButton: 'Actualizar + migrar + seed', migrateConfirm: 'Se creará una copia de seguridad de la base de datos y se ejecutarán todas las migraciones sin aplicar el seed. ¿Continuar?', migrateSeedConfirm: 'Se creará una copia de seguridad de la base de datos y después se ejecutarán todas las migraciones y el seed idempotente. ¿Continuar?', updateRunning: 'Actualización en curso ...', refresh: 'Actualizar estado', statusLabel: 'Estado de actualización', operation: 'Operación', requestedBy: 'Solicitado por', startedAt: 'Iniciado', finishedAt: 'Finalizado', commit: 'Revisión', requestAccepted: 'El runner del host aceptó la solicitud.', migrateRequestAccepted: 'El runner del host aceptó la actualización con migraciones.', migrateSeedRequestAccepted: 'El runner del host aceptó la actualización con migraciones y seed.', requestError: 'No se pudo solicitar la actualización.', loadError: 'No se pudo cargar el estado.', logTitle: 'Registro de actualización', logEmpty: 'Todavía no hay registro de actualización.', adminOnly: 'Solo los administradores pueden iniciar una actualización.', operations: { update: 'Actualización estándar', update_migrate: 'Actualización + migraciones', update_migrate_seed: 'Actualización + migraciones + seed' }, states: { idle: 'Inactivo', queued: 'En cola', running: 'En curso', succeeded: 'Correcto', failed: 'Fallido' },
      }, logs: { refresh: 'Actualizar registros' },
    },
  },
  pt: {
    admin: {
      system: {
        monitoringTitle: 'Monitorização Uptime', monitoringText: 'Abra o Uptime Kuma através do gateway HTTPS dedicado. A porta 8443 aceita apenas HTTPS.', openMonitoring: 'Abrir Uptime Kuma', httpsHint: 'Use sempre https:// na porta 8443.', updateTitle: 'Atualização do servidor', updateText: 'Obtém a versão fast-forward mais recente, cria backup, recompila a aplicação, executa migrações e verifica o serviço.', updateButton: 'Atualizar servidor', migrateButton: 'Atualizar + migrar', migrateSeedButton: 'Atualizar + migrar + seed', migrateConfirm: 'Será criado um backup da base de dados e depois serão executadas todas as migrações sem aplicar o seed. Continuar?', migrateSeedConfirm: 'Será criado um backup da base de dados e depois serão executadas todas as migrações e o seed idempotente. Continuar?', updateRunning: 'Atualização em curso ...', refresh: 'Atualizar estado', statusLabel: 'Estado da atualização', operation: 'Operação', requestedBy: 'Pedido por', startedAt: 'Iniciado', finishedAt: 'Terminado', commit: 'Revisão', requestAccepted: 'O runner do host aceitou o pedido.', migrateRequestAccepted: 'O runner do host aceitou a atualização com migrações.', migrateSeedRequestAccepted: 'O runner do host aceitou a atualização com migrações e seed.', requestError: 'Não foi possível pedir a atualização.', loadError: 'Não foi possível carregar o estado.', logTitle: 'Log da atualização', logEmpty: 'Ainda não existe log de atualização.', adminOnly: 'Apenas administradores podem iniciar uma atualização.', operations: { update: 'Atualização padrão', update_migrate: 'Atualização + migrações', update_migrate_seed: 'Atualização + migrações + seed' }, states: { idle: 'Inativo', queued: 'Na fila', running: 'Em curso', succeeded: 'Concluído', failed: 'Falhou' },
      }, logs: { refresh: 'Atualizar logs' },
    },
  },
  ru: {
    admin: {
      system: {
        monitoringTitle: 'Мониторинг Uptime', monitoringText: 'Откройте Uptime Kuma через отдельный HTTPS-шлюз. Порт 8443 принимает только HTTPS.', openMonitoring: 'Открыть Uptime Kuma', httpsHint: 'На порту 8443 всегда используйте https://.', updateTitle: 'Обновление сервера', updateText: 'Получает последнюю fast-forward версию, создает резервную копию, пересобирает приложение, выполняет миграции и проверяет готовность.', updateButton: 'Обновить сервер', migrateButton: 'Обновить + миграции', migrateSeedButton: 'Обновить + миграции + seed', migrateConfirm: 'Будет создана резервная копия базы данных, затем будут выполнены все миграции без запуска seed. Продолжить?', migrateSeedConfirm: 'Будет создана резервная копия базы данных, затем выполнены все миграции и идемпотентный seed. Продолжить?', updateRunning: 'Обновление выполняется ...', refresh: 'Обновить статус', statusLabel: 'Статус обновления', operation: 'Операция', requestedBy: 'Запросил', startedAt: 'Начато', finishedAt: 'Завершено', commit: 'Ревизия', requestAccepted: 'Host runner принял запрос.', migrateRequestAccepted: 'Host runner принял обновление с миграциями.', migrateSeedRequestAccepted: 'Host runner принял обновление с миграциями и seed.', requestError: 'Не удалось запросить обновление.', loadError: 'Не удалось загрузить статус.', logTitle: 'Журнал обновления', logEmpty: 'Журнал обновления пока отсутствует.', adminOnly: 'Только администраторы могут запускать обновление.', operations: { update: 'Обычное обновление', update_migrate: 'Обновление + миграции', update_migrate_seed: 'Обновление + миграции + seed' }, states: { idle: 'Ожидание', queued: 'В очереди', running: 'Выполняется', succeeded: 'Успешно', failed: 'Ошибка' },
      }, logs: { refresh: 'Обновить логи' },
    },
  },
  cn: {
    admin: {
      system: {
        monitoringTitle: 'Uptime 监控', monitoringText: '通过独立的 HTTPS 网关打开 Uptime Kuma。8443 端口仅接受 HTTPS。', openMonitoring: '打开 Uptime Kuma', httpsHint: '8443 端口必须使用 https://。', updateTitle: '服务器更新', updateText: '获取最新的 fast-forward 版本，创建备份，重新构建应用，执行迁移并检查服务状态。', updateButton: '更新服务器', migrateButton: '更新 + 迁移', migrateSeedButton: '更新 + 迁移 + 种子', migrateConfirm: '这将创建数据库备份并执行所有迁移，但不会运行种子。是否继续？', migrateSeedConfirm: '这将创建数据库备份，然后执行所有迁移和幂等种子。是否继续？', updateRunning: '正在更新 ...', refresh: '刷新状态', statusLabel: '更新状态', operation: '操作', requestedBy: '请求者', startedAt: '开始时间', finishedAt: '完成时间', commit: '版本', requestAccepted: '主机更新执行器已接受请求。', migrateRequestAccepted: '主机更新执行器已接受包含迁移的更新请求。', migrateSeedRequestAccepted: '主机更新执行器已接受包含迁移和种子的更新请求。', requestError: '无法请求服务器更新。', loadError: '无法加载更新状态。', logTitle: '更新日志', logEmpty: '暂无更新日志。', adminOnly: '只有管理员可以启动更新。', operations: { update: '标准更新', update_migrate: '更新 + 迁移', update_migrate_seed: '更新 + 迁移 + 种子' }, states: { idle: '空闲', queued: '已排队', running: '进行中', succeeded: '成功', failed: '失败' },
      }, logs: { refresh: '刷新日志' },
    },
  },
}
