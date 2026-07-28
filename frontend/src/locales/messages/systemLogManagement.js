export const systemLogManagementMessages = {
  en: {
    admin: { audit: { entities: { app_log: 'System log' } }, logs: {
      levelLabel: 'Log level', pathLabel: 'Request path', ipLabel: 'Client IP', sortLabel: 'Sort field', orderLabel: 'Direction',
      includeBlocked: 'Show logs from currently blocked IPs', includeBlockedHint: 'Disabled by default so repeated denied requests do not obscure actionable system events.', blockedHidden: 'Blocked IPs hidden',
      deleteFiltered: 'Delete filtered logs', deleteFilteredConfirmTitle: 'Permanently delete this log scope?', deleteFilteredConfirmText: 'This removes {count} entries matching the current filters. Audit history is retained.', deleteNow: 'Delete now', deleting: 'Deleting ...', deleteFilteredSuccess: '{count} system log entries deleted.',
      deleteOne: 'Delete entry', deleteOneConfirm: 'Permanently delete this entry?', deleteOneSuccess: 'System log entry deleted.', deleteError: 'System logs could not be deleted.', details: 'Details',
    } },
  },
  de: {
    admin: { audit: { entities: { app_log: 'Systemlog' } }, logs: {
      levelLabel: 'Log-Level', pathLabel: 'Request-Pfad', ipLabel: 'Client-IP', sortLabel: 'Sortierfeld', orderLabel: 'Reihenfolge',
      includeBlocked: 'Logs aktuell blockierter IPs anzeigen', includeBlockedHint: 'Standardmäßig aus, damit wiederholte abgewiesene Requests wichtige Systemereignisse nicht überlagern.', blockedHidden: 'Blockierte IPs ausgeblendet',
      deleteFiltered: 'Gefilterte Logs löschen', deleteFilteredConfirmTitle: 'Diesen Log-Bereich dauerhaft löschen?', deleteFilteredConfirmText: 'Dadurch werden {count} Einträge aus dem aktuellen Filterbereich entfernt. Die Änderungshistorie bleibt erhalten.', deleteNow: 'Jetzt löschen', deleting: 'Wird gelöscht ...', deleteFilteredSuccess: '{count} Systemlog-Einträge wurden gelöscht.',
      deleteOne: 'Eintrag löschen', deleteOneConfirm: 'Diesen Eintrag dauerhaft löschen?', deleteOneSuccess: 'Systemlog-Eintrag wurde gelöscht.', deleteError: 'Systemlogs konnten nicht gelöscht werden.', details: 'Details',
    } },
  },
  fr: {
    admin: { audit: { entities: { app_log: 'Journal système' } }, logs: {
      levelLabel: 'Niveau du journal', pathLabel: 'Chemin de requête', ipLabel: 'IP cliente', sortLabel: 'Champ de tri', orderLabel: 'Ordre',
      includeBlocked: 'Afficher les journaux des IP actuellement bloquées', includeBlockedHint: 'Désactivé par défaut pour éviter que les refus répétés masquent les événements importants.', blockedHidden: 'IP bloquées masquées',
      deleteFiltered: 'Supprimer les journaux filtrés', deleteFilteredConfirmTitle: 'Supprimer définitivement cette portée ?', deleteFilteredConfirmText: 'Cette action supprime {count} entrées correspondant aux filtres actuels. L’historique d’audit est conservé.', deleteNow: 'Supprimer maintenant', deleting: 'Suppression ...', deleteFilteredSuccess: '{count} entrées de journal supprimées.',
      deleteOne: 'Supprimer l’entrée', deleteOneConfirm: 'Supprimer définitivement cette entrée ?', deleteOneSuccess: 'Entrée de journal supprimée.', deleteError: 'Impossible de supprimer les journaux système.', details: 'Détails',
    } },
  },
  es: {
    admin: { audit: { entities: { app_log: 'Log del sistema' } }, logs: {
      levelLabel: 'Nivel de log', pathLabel: 'Ruta de solicitud', ipLabel: 'IP cliente', sortLabel: 'Campo de orden', orderLabel: 'Dirección',
      includeBlocked: 'Mostrar logs de IP bloqueadas actualmente', includeBlockedHint: 'Desactivado por defecto para que los rechazos repetidos no oculten eventos importantes.', blockedHidden: 'IP bloqueadas ocultas',
      deleteFiltered: 'Eliminar logs filtrados', deleteFilteredConfirmTitle: '¿Eliminar permanentemente este ámbito?', deleteFilteredConfirmText: 'Se eliminarán {count} entradas que coinciden con los filtros actuales. El historial de auditoría se conserva.', deleteNow: 'Eliminar ahora', deleting: 'Eliminando ...', deleteFilteredSuccess: 'Se eliminaron {count} entradas de log.',
      deleteOne: 'Eliminar entrada', deleteOneConfirm: '¿Eliminar permanentemente esta entrada?', deleteOneSuccess: 'Entrada de log eliminada.', deleteError: 'No se pudieron eliminar los logs del sistema.', details: 'Detalles',
    } },
  },
  pt: {
    admin: { audit: { entities: { app_log: 'Log do sistema' } }, logs: {
      levelLabel: 'Nível do log', pathLabel: 'Caminho do pedido', ipLabel: 'IP do cliente', sortLabel: 'Campo de ordenação', orderLabel: 'Direção',
      includeBlocked: 'Mostrar logs de IPs atualmente bloqueados', includeBlockedHint: 'Desativado por padrão para que recusas repetidas não ocultem eventos importantes.', blockedHidden: 'IPs bloqueados ocultos',
      deleteFiltered: 'Eliminar logs filtrados', deleteFilteredConfirmTitle: 'Eliminar permanentemente este âmbito?', deleteFilteredConfirmText: 'Remove {count} entradas que correspondem aos filtros atuais. O histórico de auditoria é mantido.', deleteNow: 'Eliminar agora', deleting: 'A eliminar ...', deleteFilteredSuccess: '{count} entradas de log eliminadas.',
      deleteOne: 'Eliminar entrada', deleteOneConfirm: 'Eliminar permanentemente esta entrada?', deleteOneSuccess: 'Entrada de log eliminada.', deleteError: 'Não foi possível eliminar os logs do sistema.', details: 'Detalhes',
    } },
  },
  ru: {
    admin: { audit: { entities: { app_log: 'Системный лог' } }, logs: {
      levelLabel: 'Уровень лога', pathLabel: 'Путь запроса', ipLabel: 'IP клиента', sortLabel: 'Поле сортировки', orderLabel: 'Порядок',
      includeBlocked: 'Показывать логи активных заблокированных IP', includeBlockedHint: 'По умолчанию выключено, чтобы повторные отклонённые запросы не скрывали важные события.', blockedHidden: 'Заблокированные IP скрыты',
      deleteFiltered: 'Удалить отфильтрованные логи', deleteFilteredConfirmTitle: 'Удалить эту область навсегда?', deleteFilteredConfirmText: 'Будет удалено записей: {count}. История аудита сохранится.', deleteNow: 'Удалить', deleting: 'Удаление ...', deleteFilteredSuccess: 'Удалено записей системного лога: {count}.',
      deleteOne: 'Удалить запись', deleteOneConfirm: 'Удалить эту запись навсегда?', deleteOneSuccess: 'Запись системного лога удалена.', deleteError: 'Не удалось удалить системные логи.', details: 'Подробности',
    } },
  },
  cn: {
    admin: { audit: { entities: { app_log: '系统日志' } }, logs: {
      levelLabel: '日志级别', pathLabel: '请求路径', ipLabel: '客户端 IP', sortLabel: '排序字段', orderLabel: '顺序',
      includeBlocked: '显示当前已封禁 IP 的日志', includeBlockedHint: '默认关闭，避免重复拒绝请求掩盖重要系统事件。', blockedHidden: '已隐藏封禁 IP',
      deleteFiltered: '删除筛选日志', deleteFilteredConfirmTitle: '永久删除当前日志范围？', deleteFilteredConfirmText: '将删除符合当前筛选条件的 {count} 条记录，审计历史会保留。', deleteNow: '立即删除', deleting: '正在删除 ...', deleteFilteredSuccess: '已删除 {count} 条系统日志。',
      deleteOne: '删除记录', deleteOneConfirm: '永久删除此记录？', deleteOneSuccess: '系统日志记录已删除。', deleteError: '无法删除系统日志。', details: '详情',
    } },
  },
}
