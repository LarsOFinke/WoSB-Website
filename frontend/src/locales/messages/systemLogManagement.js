export const systemLogManagementMessages = {
  en: {
    admin: {
      audit: { entities: { security_event: 'IP-ban signal' } },
      logs: {
        privacyTitle: 'Purpose-limited security data',
        privacyText: 'Only the IP address, UTC day, coarse ban-relevant signal and daily count are retained for 7 calendar days. Routes, query strings, user agents, request IDs, payloads and exception details are never stored here. Signals are deleted immediately when the IP is blocked.',
      },
    },
  },
  de: {
    admin: {
      audit: { entities: { security_event: 'IP-Sperrsignal' } },
      logs: {
        privacyTitle: 'Zweckgebundene Sicherheitsdaten',
        privacyText: 'Gespeichert werden für höchstens 7 Kalendertage nur IP-Adresse, UTC-Tag, grobes sperrrelevantes Signal und Tageszähler. Routen, Query-Strings, User-Agents, Request-IDs, Inhalte und Exception-Details werden hier nie gespeichert. Beim Sperren der IP werden ihre Signale sofort gelöscht.',
      },
    },
  },
  fr: { admin: { audit: { entities: { security_event: 'Signal de blocage IP' } }, logs: { privacyTitle: 'Données de sécurité limitées à leur finalité', privacyText: 'Seuls l’adresse IP, le jour UTC, un signal général utile au blocage et son compteur journalier sont conservés pendant 7 jours calendaires. Les routes, requêtes, agents utilisateur, identifiants de requête, contenus et exceptions ne sont jamais stockés ici. Les signaux sont supprimés dès que l’IP est bloquée.' } } },
  es: { admin: { audit: { entities: { security_event: 'Señal de bloqueo IP' } }, logs: { privacyTitle: 'Datos de seguridad limitados a su finalidad', privacyText: 'Solo se conservan durante 7 días naturales la dirección IP, el día UTC, una señal general relevante para el bloqueo y su contador diario. No se guardan rutas, consultas, agentes de usuario, identificadores de solicitud, contenidos ni excepciones. Las señales se borran al bloquear la IP.' } } },
  pt: { admin: { audit: { entities: { security_event: 'Sinal de bloqueio de IP' } }, logs: { privacyTitle: 'Dados de segurança limitados à finalidade', privacyText: 'Apenas o endereço IP, o dia UTC, um sinal geral relevante para bloqueio e o contador diário são mantidos durante 7 dias de calendário. Rotas, consultas, user agents, IDs de pedido, conteúdos e exceções nunca são guardados aqui. Os sinais são apagados quando o IP é bloqueado.' } } },
  ru: { admin: { audit: { entities: { security_event: 'Сигнал блокировки IP' } }, logs: { privacyTitle: 'Данные безопасности только по назначению', privacyText: 'В течение 7 календарных дней сохраняются только IP-адрес, день UTC, общий сигнал для решения о блокировке и его суточный счётчик. Маршруты, строки запроса, user-agent, ID запросов, содержимое и исключения здесь не сохраняются. После блокировки IP сигналы удаляются.' } } },
  cn: { admin: { audit: { entities: { security_event: 'IP 封禁信号' } }, logs: { privacyTitle: '仅限封禁目的的安全数据', privacyText: '仅保留 IP 地址、UTC 日期、粗粒度封禁信号及每日计数，最长 7 个日历日。不会保存路由、查询字符串、User-Agent、请求 ID、内容或异常详情。IP 被封禁后，其信号会立即删除。' } } },
}
