export const systemLogManagementMessages = {
  en: {
    admin: {
      audit: { entities: { security_event: 'IP-ban signal' } },
      logs: {
        privacyTitle: 'Purpose-limited security data',
        privacyText: 'The IP address, UTC day, reason, safe route template or fixed probe category, and daily count are retained for 7 calendar days. Raw paths, query strings, user agents, request IDs, payloads and exception details are never stored. Signals are deleted immediately when the IP is blocked.',
      },
    },
  },
  de: {
    admin: {
      audit: { entities: { security_event: 'IP-Sperrsignal' } },
      logs: {
        privacyTitle: 'Zweckgebundene Sicherheitsdaten',
        privacyText: 'Für höchstens 7 Kalendertage werden IP-Adresse, UTC-Tag, Grund, sicheres Routen-Template oder feste Scan-Kategorie und Tageszähler gespeichert. Freie Pfade, Query-Strings, User-Agents, Request-IDs, Inhalte und Exception-Details werden nie gespeichert. Beim Sperren der IP werden ihre Signale sofort gelöscht.',
      },
    },
  },
  fr: { admin: { audit: { entities: { security_event: 'Signal de blocage IP' } }, logs: { privacyTitle: 'Données de sécurité limitées à leur finalité', privacyText: 'Pendant 7 jours sont conservés l’adresse IP, le jour UTC, le motif, un modèle de route sûr ou une catégorie de sonde fixe et le compteur journalier. Les chemins bruts, requêtes, agents utilisateur, identifiants, contenus et exceptions ne sont jamais stockés. Les signaux sont supprimés dès que l’IP est bloquée.' } } },
  es: { admin: { audit: { entities: { security_event: 'Señal de bloqueo IP' } }, logs: { privacyTitle: 'Datos de seguridad limitados a su finalidad', privacyText: 'Durante 7 días se conservan la IP, el día UTC, el motivo, una plantilla de ruta segura o categoría fija de sondeo y el contador diario. No se guardan rutas sin procesar, consultas, agentes de usuario, identificadores, contenidos ni excepciones. Las señales se borran al bloquear la IP.' } } },
  pt: { admin: { audit: { entities: { security_event: 'Sinal de bloqueio de IP' } }, logs: { privacyTitle: 'Dados de segurança limitados à finalidade', privacyText: 'Durante 7 dias são mantidos o IP, dia UTC, motivo, modelo de rota seguro ou categoria fixa de sondagem e contador diário. Caminhos brutos, consultas, user agents, IDs, conteúdos e exceções nunca são guardados. Os sinais são apagados quando o IP é bloqueado.' } } },
  ru: { admin: { audit: { entities: { security_event: 'Сигнал блокировки IP' } }, logs: { privacyTitle: 'Данные безопасности только по назначению', privacyText: 'На 7 дней сохраняются IP, день UTC, причина, безопасный шаблон маршрута или фиксированная категория сканирования и суточный счётчик. Необработанные пути, строки запроса, user-agent, ID, содержимое и исключения не сохраняются. После блокировки IP сигналы удаляются.' } } },
  cn: { admin: { audit: { entities: { security_event: 'IP 封禁信号' } }, logs: { privacyTitle: '仅限封禁目的的安全数据', privacyText: 'IP、UTC 日期、原因、安全路由模板或固定探测类别及每日计数最多保留 7 天。不会保存原始路径、查询字符串、User-Agent、请求 ID、内容或异常。IP 被封禁后，其信号会立即删除。' } } },
}
