export const localeCompletenessMessages = {
  en: {
    forum: {
      categories: {
        training: 'Training',
        logistics: 'Logistics',
        loistics: 'Logistics',
      },
    },
  },
  de: {
    common: { modules: 'Module', groups: 'Gruppensuche', myGroupSearches: 'Meine Gruppensuchen' },
    logs: { clientIp: 'Client-IP', queryString: 'Query-String' },
    forum: { categories: { training: 'Training', logistics: 'Logistik', loistics: 'Logistik' } },
    groups: {
      fields: { schedule: 'Zeitraum' },
      list: { title: 'Gruppensuche', newGroup: 'Neue Gruppensuche', announcementMode: 'Gruppensuche' },
      create: { title: 'Neue Gruppensuche', save: 'Gruppensuche erstellen', timeRangeInvalid: 'Die Endzeit muss nach der Startzeit liegen.', sections: { schedule: 'Zeitraum' } },
      detail: { announcementEyebrow: 'Gruppensuche', overviewTitle: 'Überblick', joinClosedTitle: 'Anmeldung nicht möglich' },
    },
    myGroups: { title: 'Meine Gruppensuchen', manageTitle: 'Eigene Gruppensuchen', profileCardTitle: 'Meine Gruppensuchen', summaryOne: '1 eigene Gruppensuche', summaryMany: '{count} eigene Gruppensuchen' },
    admin: { content: { announcements: 'Gruppensuchen', closeError: 'Gruppensuche konnte nicht geschlossen werden.' } },
    buildEmbeds: { sectionTitle: 'Build-Referenzen', selected: 'Ausgewähltes Build', linkedEyebrow: 'Guide-Referenzen', linkedCardEyebrow: 'Build-Referenz', inlineEyebrow: 'Eingebettetes Build', layouts: { compact: 'Kompakt', card: 'Karte' } },
    builds: {
      create: { stats: { durability: 'Haltbarkeit {value}', speed: 'Geschwindigkeit {value} kn' }, weapons: { capacity: '{count}/{max} montiert' } },
      stats: { breakdownTitle: 'Build-Stat-Aufschlüsselung', baseAndModifier: 'Basis {base} · Modifikator {modifier}', columns: { stat: 'Wert', base: 'Basis', modifier: 'Modifikator', effective: 'Effektiv' } },
      statLabels: {
        durability: 'Haltbarkeit', speed_knots: 'Geschwindigkeit', maneuverability: 'Wendigkeit', hold_capacity: 'Laderaum', displacement_tons: 'Verdrängung', reload_pct: 'Nachladegeschwindigkeit', weapon_range_pct: 'Kanonenreichweite', cannon_damage_pct: 'Kanonen-Schaden', low_hp_damage_pct: 'Schaden unter 50 % HP', fire_damage_pct: 'Feuerschaden', siege_damage_pct: 'Belagerungsschaden', ram_damage_pct: 'Rammschaden', repair_efficiency_pct: 'Reparatureffizienz', sail_hp_pct: 'Segelhaltbarkeit', fire_resistance_pct: 'Feuerresistenz', cargo_loss_reduction_pct: 'Frachtverlust-Reduktion', hold_slots: 'Laderaumplätze', fire_risk_pct: 'Brandrisiko',
      },
    },
    fleets: { directory: { assignment: 'Einteilung', availability: 'Verfügbarkeit', timezone: 'Zeitzone', adminNote: 'Interne Notiz' } },
  },
  fr: {
    common: { modules: 'Sections', groups: 'Recherche de groupe', myGroupSearches: 'Mes recherches de groupe' },
    logs: { clientIp: 'IP client', queryString: 'Chaîne de requête' },
    forum: { categories: { training: 'Entraînement', logistics: 'Logistique', loistics: 'Logistique' } },
    groups: {
      fields: { schedule: 'Créneau' },
      list: { title: 'Recherche de groupe', newGroup: 'Nouvelle recherche', announcementMode: 'Recherche de groupe' },
      create: { title: 'Nouvelle recherche de groupe', save: 'Créer la recherche', timeRangeInvalid: 'L’heure de fin doit être postérieure au début.', sections: { schedule: 'Créneau' } },
      detail: { announcementEyebrow: 'Recherche de groupe', overviewTitle: 'Aperçu', joinClosedTitle: 'Inscription indisponible' },
    },
    myGroups: { title: 'Mes recherches de groupe', manageTitle: 'Mes recherches', profileCardTitle: 'Mes recherches de groupe', summaryOne: '1 recherche créée', summaryMany: '{count} recherches créées' },
    admin: { content: { announcements: 'Recherches de groupe', closeError: 'Impossible de fermer la recherche de groupe.' } },
    buildEmbeds: { sectionTitle: 'Références de build', selected: 'Build sélectionné', linkedEyebrow: 'Références du guide', linkedCardEyebrow: 'Référence de build', inlineEyebrow: 'Build intégré', layouts: { compact: 'Condensé', card: 'Carte' } },
    builds: {
      create: { stats: { durability: 'Durabilité {value}', speed: 'Vitesse {value} nd' }, weapons: { capacity: '{count}/{max} installés' } },
      stats: { breakdownTitle: 'Détail des stats du build', baseAndModifier: 'Base {base} · Modificateur {modifier}', columns: { stat: 'Statistique', base: 'Valeur de base', modifier: 'Modificateur', effective: 'Effectif' } },
      statLabels: {
        durability: 'Durabilité', speed_knots: 'Vitesse', maneuverability: 'Maniabilité', hold_capacity: 'Cale', displacement_tons: 'Déplacement', reload_pct: 'Vitesse de rechargement', weapon_range_pct: 'Portée des canons', cannon_damage_pct: 'Dégâts des canons', low_hp_damage_pct: 'Dégâts sous 50 % PV', fire_damage_pct: 'Dégâts de feu', siege_damage_pct: 'Dégâts de siège', ram_damage_pct: 'Dégâts d’éperonnage', repair_efficiency_pct: 'Efficacité des réparations', sail_hp_pct: 'Résistance des voiles', fire_resistance_pct: 'Résistance au feu', cargo_loss_reduction_pct: 'Réduction des pertes de cargaison', hold_slots: 'Emplacements de cale', fire_risk_pct: 'Risque d’incendie',
      },
    },
    fleets: { directory: { assignment: 'Affectation', availability: 'Disponibilité', timezone: 'Fuseau horaire', adminNote: 'Note interne' } },
  },
  es: {
    common: { modules: 'Módulos', groups: 'Búsqueda de grupo', myGroupSearches: 'Mis búsquedas de grupo' },
    logs: { clientIp: 'IP del cliente', queryString: 'Consulta' },
    forum: { categories: { training: 'Entrenamiento', logistics: 'Logística', loistics: 'Logística' } },
    groups: {
      fields: { schedule: 'Horario' },
      list: { title: 'Búsqueda de grupo', newGroup: 'Nueva búsqueda', announcementMode: 'Búsqueda de grupo' },
      create: { title: 'Nueva búsqueda de grupo', save: 'Crear búsqueda', timeRangeInvalid: 'La hora de fin debe ser posterior al inicio.', sections: { schedule: 'Horario' } },
      detail: { announcementEyebrow: 'Búsqueda de grupo', overviewTitle: 'Resumen', joinClosedTitle: 'Inscripción no disponible' },
    },
    myGroups: { title: 'Mis búsquedas de grupo', manageTitle: 'Tus búsquedas de grupo', profileCardTitle: 'Mis búsquedas de grupo', summaryOne: '1 búsqueda propia', summaryMany: '{count} búsquedas propias' },
    admin: { content: { announcements: 'Búsquedas de grupo', closeError: 'No se pudo cerrar la búsqueda de grupo.' } },
    buildEmbeds: { sectionTitle: 'Referencias de build', selected: 'Build seleccionado', linkedEyebrow: 'Referencias de la guía', linkedCardEyebrow: 'Referencia de build', inlineEyebrow: 'Build incrustado', layouts: { compact: 'Compacto', card: 'Tarjeta' } },
    builds: {
      create: { stats: { durability: 'Durabilidad {value}', speed: 'Velocidad {value} kn' }, weapons: { capacity: '{count}/{max} montadas' } },
      stats: { breakdownTitle: 'Desglose de estadísticas del build', baseAndModifier: 'Base {base} · Modificador {modifier}', columns: { stat: 'Estadística', base: 'Valor base', modifier: 'Modificador', effective: 'Efectivo' } },
      statLabels: {
        durability: 'Durabilidad', speed_knots: 'Velocidad', maneuverability: 'Maniobrabilidad', hold_capacity: 'Bodega', displacement_tons: 'Desplazamiento', reload_pct: 'Velocidad de recarga', weapon_range_pct: 'Alcance de cañones', cannon_damage_pct: 'Daño de cañones', low_hp_damage_pct: 'Daño bajo 50 % HP', fire_damage_pct: 'Daño de fuego', siege_damage_pct: 'Daño de asedio', ram_damage_pct: 'Daño de embestida', repair_efficiency_pct: 'Eficiencia de reparación', sail_hp_pct: 'Durabilidad de velas', fire_resistance_pct: 'Resistencia al fuego', cargo_loss_reduction_pct: 'Reducción de pérdida de carga', hold_slots: 'Espacios de bodega', fire_risk_pct: 'Riesgo de incendio',
      },
    },
    fleets: { directory: { assignment: 'Asignación', availability: 'Disponibilidad', timezone: 'Zona horaria', adminNote: 'Nota interna' } },
  },
  pt: {
    common: { modules: 'Módulos', groups: 'Procura de grupo', myGroupSearches: 'As minhas procuras de grupo' },
    logs: { clientIp: 'IP do cliente', queryString: 'Consulta' },
    forum: { categories: { training: 'Treino', logistics: 'Logística', loistics: 'Logística' } },
    groups: {
      fields: { schedule: 'Horário' },
      list: { title: 'Procura de grupo', newGroup: 'Nova procura', announcementMode: 'Procura de grupo' },
      create: { title: 'Nova procura de grupo', save: 'Criar procura', timeRangeInvalid: 'A hora de fim deve ser posterior ao início.', sections: { schedule: 'Horário' } },
      detail: { announcementEyebrow: 'Procura de grupo', overviewTitle: 'Resumo', joinClosedTitle: 'Inscrição indisponível' },
    },
    myGroups: { title: 'As minhas procuras de grupo', manageTitle: 'As suas procuras de grupo', profileCardTitle: 'As minhas procuras de grupo', summaryOne: '1 procura própria', summaryMany: '{count} procuras próprias' },
    admin: { content: { announcements: 'Procuras de grupo', closeError: 'Não foi possível fechar a procura de grupo.' } },
    buildEmbeds: { sectionTitle: 'Referências de build', selected: 'Build selecionado', linkedEyebrow: 'Referências do guia', linkedCardEyebrow: 'Referência de build', inlineEyebrow: 'Build incorporado', layouts: { compact: 'Compacto', card: 'Cartão' } },
    builds: {
      create: { stats: { durability: 'Durabilidade {value}', speed: 'Velocidade {value} kn' }, weapons: { capacity: '{count}/{max} montadas' } },
      stats: { breakdownTitle: 'Detalhe das estatísticas do build', baseAndModifier: 'Base {base} · Modificador {modifier}', columns: { stat: 'Estatística', base: 'Valor base', modifier: 'Modificador', effective: 'Efetivo' } },
      statLabels: {
        durability: 'Durabilidade', speed_knots: 'Velocidade', maneuverability: 'Manobrabilidade', hold_capacity: 'Porão', displacement_tons: 'Deslocamento', reload_pct: 'Velocidade de recarga', weapon_range_pct: 'Alcance dos canhões', cannon_damage_pct: 'Dano dos canhões', low_hp_damage_pct: 'Dano abaixo de 50 % HP', fire_damage_pct: 'Dano de fogo', siege_damage_pct: 'Dano de cerco', ram_damage_pct: 'Dano de abalroamento', repair_efficiency_pct: 'Eficiência de reparação', sail_hp_pct: 'Durabilidade das velas', fire_resistance_pct: 'Resistência ao fogo', cargo_loss_reduction_pct: 'Redução de perda de carga', hold_slots: 'Espaços do porão', fire_risk_pct: 'Risco de incêndio',
      },
    },
    fleets: { directory: { assignment: 'Atribuição', availability: 'Disponibilidade', timezone: 'Fuso horário', adminNote: 'Nota interna' } },
  },
  ru: {
    common: { modules: 'Модули', groups: 'Поиск группы', myGroupSearches: 'Мои поиски группы' },
    logs: { clientIp: 'IP клиента', queryString: 'Строка запроса' },
    forum: { categories: { training: 'Тренировка', logistics: 'Логистика', loistics: 'Логистика' } },
    groups: {
      fields: { schedule: 'Время' },
      list: { title: 'Поиск группы', newGroup: 'Новый поиск', announcementMode: 'Поиск группы' },
      create: { title: 'Новый поиск группы', save: 'Создать поиск', timeRangeInvalid: 'Время окончания должно быть позже начала.', sections: { schedule: 'Время' } },
      detail: { announcementEyebrow: 'Поиск группы', overviewTitle: 'Обзор', joinClosedTitle: 'Запись недоступна' },
    },
    myGroups: { title: 'Мои поиски группы', manageTitle: 'Ваши поиски группы', profileCardTitle: 'Мои поиски группы', summaryOne: '1 ваш поиск', summaryMany: '{count} ваших поисков' },
    admin: { content: { announcements: 'Поиски группы', closeError: 'Не удалось закрыть поиск группы.' } },
    buildEmbeds: { sectionTitle: 'Ссылки на билды', selected: 'Выбранный билд', linkedEyebrow: 'Ссылки гайда', linkedCardEyebrow: 'Ссылка на билд', inlineEyebrow: 'Встроенный билд', layouts: { compact: 'Компактно', card: 'Карточка' } },
    builds: {
      create: { stats: { durability: 'Прочность {value}', speed: 'Скорость {value} уз.' }, weapons: { capacity: '{count}/{max} установлено' } },
      stats: { breakdownTitle: 'Разбор характеристик билда', baseAndModifier: 'База {base} · Модификатор {modifier}', columns: { stat: 'Стат', base: 'База', modifier: 'Модификатор', effective: 'Итог' } },
      statLabels: {
        durability: 'Прочность', speed_knots: 'Скорость', maneuverability: 'Маневренность', hold_capacity: 'Трюм', displacement_tons: 'Водоизмещение', reload_pct: 'Скорость перезарядки', weapon_range_pct: 'Дальность пушек', cannon_damage_pct: 'Урон пушек', low_hp_damage_pct: 'Урон ниже 50 % HP', fire_damage_pct: 'Урон от огня', siege_damage_pct: 'Осадный урон', ram_damage_pct: 'Урон тараном', repair_efficiency_pct: 'Эффективность ремонта', sail_hp_pct: 'Прочность парусов', fire_resistance_pct: 'Сопротивление огню', cargo_loss_reduction_pct: 'Снижение потерь груза', hold_slots: 'Слоты трюма', fire_risk_pct: 'Риск пожара',
      },
    },
    fleets: { directory: { assignment: 'Назначение', availability: 'Доступность', timezone: 'Часовой пояс', adminNote: 'Внутренняя заметка' } },
  },
  cn: {
    common: { modules: '模块', groups: '组队搜索', myGroupSearches: '我的组队搜索' },
    logs: { clientIp: '客户端 IP', queryString: '查询字符串' },
    forum: { categories: { training: '训练', logistics: '后勤', loistics: '后勤' } },
    groups: {
      fields: { schedule: '时间段' },
      list: { title: '组队搜索', newGroup: '新的组队搜索', announcementMode: '组队搜索' },
      create: { title: '新的组队搜索', save: '创建组队搜索', timeRangeInvalid: '结束时间必须晚于开始时间。', sections: { schedule: '时间段' } },
      detail: { announcementEyebrow: '组队搜索', overviewTitle: '概览', joinClosedTitle: '无法报名' },
    },
    myGroups: { title: '我的组队搜索', manageTitle: '你的组队搜索', profileCardTitle: '我的组队搜索', summaryOne: '1 个自己的组队搜索', summaryMany: '{count} 个自己的组队搜索' },
    admin: { content: { announcements: '组队搜索', closeError: '无法关闭组队搜索。' } },
    buildEmbeds: { sectionTitle: 'Build 引用', selected: '已选择的 Build', linkedEyebrow: '指南引用', linkedCardEyebrow: 'Build 引用', inlineEyebrow: '嵌入式 Build', layouts: { compact: '紧凑', card: '卡片' } },
    builds: {
      create: { stats: { durability: '耐久 {value}', speed: '速度 {value} 节' }, weapons: { capacity: '{count}/{max} 已装备' } },
      stats: { breakdownTitle: 'Build 属性明细', baseAndModifier: '基础 {base} · 修正 {modifier}', columns: { stat: '属性', base: '基础', modifier: '修正', effective: '最终' } },
      statLabels: {
        durability: '耐久', speed_knots: '速度', maneuverability: '机动性', hold_capacity: '货舱', displacement_tons: '排水量', reload_pct: '装填速度', weapon_range_pct: '火炮射程', cannon_damage_pct: '火炮伤害', low_hp_damage_pct: '低于 50% HP 伤害', fire_damage_pct: '火焰伤害', siege_damage_pct: '攻城伤害', ram_damage_pct: '撞击伤害', repair_efficiency_pct: '维修效率', sail_hp_pct: '船帆耐久', fire_resistance_pct: '火焰抗性', cargo_loss_reduction_pct: '货物损失降低', hold_slots: '货舱槽位', fire_risk_pct: '起火风险',
      },
    },
    fleets: { directory: { assignment: '分配', availability: '可用时间', timezone: '时区', adminNote: '内部备注' } },
  },
}
