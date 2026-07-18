export const discoveryModulesMessages = {
  en: {
    discovery: {
      chooseFirst: 'Choose a direction', reset: 'Reset', results: 'Results',
      builds: {
        title: 'What do you need your ship for?', hint: 'Choose an operation or role. Search and build type remain available for precise filtering.', toolbarLabel: 'Search and filter builds',
        groups: { useCase: 'Operation', role: 'Role & characteristics' },
        showAll: 'Show all builds', showAllHint: 'Open the complete build library without a discovery filter.', allResults: 'All builds',
        formTitle: 'Operations and roles', formHint: 'Choose up to six matching classifications. These power the library filters.', selectionCount: '{count}/{max} selected',
        resultEyebrow: 'Calculated result', liveResult: 'Live result', inputEyebrow: 'Build inputs', configureTitle: 'Configure build', configureHint: 'All selections are grouped compactly below the live result.',
        tags: {
          port_battle: { label: 'Port Battle', description: 'Coordinated harbor assaults and defence.' },
          pve_solo: { label: 'PvE Solo', description: 'Reliable missions without a group.' },
          pve_group: { label: 'PvE Group', description: 'Loadouts for coordinated crews.' },
          pve_instanced: { label: 'PvE Instanced', description: 'Focused scenarios and encounters.' },
          pvp_solo: { label: 'PvP Solo', description: 'Independent hunting and duels.' },
          pvp_group: { label: 'PvP Group', description: 'Small-fleet coordination.' },
          pvp_instanced: { label: 'PvP Instanced', description: 'Structured competitive battles.' },
          trading: { label: 'Trading', description: 'Profit, range and cargo security.' },
          fast: { label: 'Fast', description: 'Speed, pursuit and disengagement.' },
          combat: { label: 'Combat', description: 'Direct damage and pressure.' },
          heavy: { label: 'Heavy', description: 'Armour and staying power.' },
          transport: { label: 'Transport', description: 'Cargo and fleet logistics.' },
          siege: { label: 'Siege', description: 'Mortars and fortification pressure.' },
          imperial: { label: 'Imperial', description: 'Empire-focused equipment and crews.' },
        },
      },
      guides: {
        title: 'What would you like to master?', hint: 'Start with a topic. Guides only appear after a choice or search.',
        groups: { start: 'First steps', combat: 'Ships & combat', fleet: 'Fleet life' },
        showAll: 'Show all guides', showAllHint: 'Browse the complete knowledge library.', allResults: 'All guides',
        formTitle: 'Choose a category', formHint: 'The category determines where members discover this guide.',
        categories: {
          new_captains: 'Orientation for new captains.', general: 'Core mechanics and practical basics.', builds: 'Ship choices, equipment and build design.', pve: 'Missions, enemies and PvE tactics.', pvp: 'Player combat and decision-making.', port_battles: 'Preparation and execution for port battles.', fleet_operations: 'Roles, formations and coordinated operations.', economy: 'Trading routes, resources and fleet logistics.',
        },
      },
      specialists: { regularCount: '{count}/{max} regular slots', gingerHint: 'Extra specialist: resolves conflicts and uses no regular slot.' },
    },
    builds: { list: { title: 'Build library', subtitle: 'Find builds by operation, role, ship or technical type.', empty: 'No matching builds found.' } },
    guides: {
      list: { title: 'Guide library', subtitle: 'Find clear guidance for your next voyage, battle or fleet operation.', empty: 'No matching guides found.' },
      categories: { new_captains: 'New captains', fleet_operations: 'Fleet operations', port_battles: 'Port Battles', pve: 'PvE', pvp: 'PvP' },
    },
  },
  de: {
    discovery: {
      chooseFirst: 'Richtung wählen', reset: 'Zurücksetzen', results: 'Ergebnisse',
      builds: {
        title: 'Wofür brauchst du dein Schiff?', hint: 'Wähle Einsatz oder Rolle. Suche und Build-Typ bleiben für die Feinfilterung verfügbar.', toolbarLabel: 'Builds suchen und filtern',
        groups: { useCase: 'Einsatz', role: 'Rolle & Eigenschaften' },
        showAll: 'Alle Builds anzeigen', showAllHint: 'Die vollständige Build-Bibliothek ohne Discovery-Filter öffnen.', allResults: 'Alle Builds',
        formTitle: 'Einsätze und Rollen', formHint: 'Wähle bis zu sechs passende Einordnungen. Sie steuern später die Bibliotheksfilter.', selectionCount: '{count}/{max} ausgewählt',
        resultEyebrow: 'Berechnetes Resultat', liveResult: 'Live-Ergebnis', inputEyebrow: 'Build-Eingaben', configureTitle: 'Build konfigurieren', configureHint: 'Alle Auswahlen sind kompakt unter dem Live-Ergebnis gebündelt.',
        tags: {
          port_battle: { label: 'Hafenschlacht', description: 'Koordinierter Hafenangriff und Verteidigung.' },
          pve_solo: { label: 'PvE Solo-Modus', description: 'Verlässliche Missionen ohne Gruppe.' },
          pve_group: { label: 'PvE Gruppe', description: 'Loadouts für abgestimmte Crews.' },
          pve_instanced: { label: 'PvE Instanz', description: 'Fokussierte Szenarien und Begegnungen.' },
          pvp_solo: { label: 'PvP Solo-Modus', description: 'Eigenständige Jagd und Duelle.' },
          pvp_group: { label: 'PvP Gruppe', description: 'Koordination in kleinen Flotten.' },
          pvp_instanced: { label: 'PvP Instanz', description: 'Strukturierte kompetitive Gefechte.' },
          trading: { label: 'Handel', description: 'Profit, Reichweite und Ladungsschutz.' },
          fast: { label: 'Schnell', description: 'Tempo, Verfolgung und Rückzug.' },
          combat: { label: 'Kampf', description: 'Direkter Schaden und Gefechtsdruck.' },
          heavy: { label: 'Schwer', description: 'Panzerung und Standfestigkeit.' },
          transport: { label: 'Transporter', description: 'Fracht und Flottenlogistik.' },
          siege: { label: 'Belagerung', description: 'Mörser und Druck auf Befestigungen.' },
          imperial: { label: 'Imperial-Set', description: 'Auf das Imperium ausgerichtete Ausrüstung.' },
        },
      },
      guides: {
        title: 'Was möchtest du meistern?', hint: 'Starte mit einem Thema. Guides erscheinen erst nach Auswahl oder Suche.',
        groups: { start: 'Erste Schritte', combat: 'Schiffe & Kampf', fleet: 'Flottenleben' },
        showAll: 'Alle Guides anzeigen', showAllHint: 'Die vollständige Wissensbibliothek durchsehen.', allResults: 'Alle Guides',
        formTitle: 'Kategorie wählen', formHint: 'Die Kategorie bestimmt, wo Mitglieder diesen Guide entdecken.',
        categories: {
          new_captains: 'Orientierung für neue Kapitäne.', general: 'Grundmechaniken und praktische Basics.', builds: 'Schiffswahl, Ausrüstung und Build-Planung.', pve: 'Missionen, Gegner und PvE-Taktiken.', pvp: 'Spielergefechte und Entscheidungen.', port_battles: 'Vorbereitung und Ablauf von Port Battles.', fleet_operations: 'Rollen, Formationen und koordinierte Einsätze.', economy: 'Handelsrouten, Ressourcen und Flottenlogistik.',
        },
      },
      specialists: { regularCount: '{count}/{max} reguläre Slots', gingerHint: 'Extra-Spezialist: löst Konflikte und belegt keinen regulären Slot.' },
    },
    builds: { list: { title: 'Build-Bibliothek', subtitle: 'Finde passende Builds nach Einsatz, Rolle, Schiff oder technischem Typ.', empty: 'Keine passenden Builds gefunden.' } },
    guides: {
      list: { title: 'Guide-Bibliothek', subtitle: 'Finde klare Anleitungen für deine nächste Fahrt, Schlacht oder Flottenoperation.', empty: 'Keine passenden Guides gefunden.' },
      categories: { new_captains: 'Neue Kapitäne', fleet_operations: 'Flottenoperationen', port_battles: 'Hafenschlachten', pve: 'PvE', pvp: 'PvP' },
    },
  },
  fr: { discovery: { reset: 'Réinitialiser', results: 'Résultats', builds: { showAll: 'Afficher tous les builds', selectionCount: '{count}/{max} sélectionnés', tags: { pve_solo: { label: 'JcE solo' }, pve_group: { label: 'JcE en groupe' }, pve_instanced: { label: 'JcE instancié' }, pvp_solo: { label: 'JcJ solo' }, pvp_group: { label: 'JcJ en groupe' }, pvp_instanced: { label: 'JcJ instancié', description: 'Combats compétitifs structurés.' }, fast: { label: 'Rapide' }, heavy: { label: 'Lourd' }, siege: { label: 'Siège' }, imperial: { label: 'Impérial' } } }, guides: { groups: { start: 'Premiers pas' }, showAll: 'Afficher tous les guides' }, specialists: { regularCount: '{count}/{max} emplacements réguliers' } } },
  es: { discovery: { reset: 'Restablecer', results: 'Resultados', builds: { showAll: 'Mostrar todos los builds', selectionCount: '{count}/{max} seleccionados', tags: { pve_solo: { label: 'JcE en solitario' }, pve_group: { label: 'JcE en grupo' }, pve_instanced: { label: 'JcE instanciado' }, pvp_solo: { label: 'JcJ en solitario' }, pvp_group: { label: 'JcJ en grupo' }, pvp_instanced: { label: 'JcJ instanciado', description: 'Batallas competitivas estructuradas.' }, fast: { label: 'Rápido' }, heavy: { label: 'Pesado' }, siege: { label: 'Asedio' }, imperial: { label: 'Nave imperial' } } }, guides: { groups: { start: 'Primeros pasos' }, showAll: 'Mostrar todas las guías' }, specialists: { regularCount: '{count}/{max} espacios regulares' } } },
  pt: { discovery: { reset: 'Repor', results: 'Resultados', builds: { showAll: 'Mostrar todos os builds', selectionCount: '{count}/{max} selecionados', tags: { pve_solo: { label: 'PvE a solo' }, pve_group: { label: 'PvE em grupo' }, pve_instanced: { label: 'PvE instanciado' }, pvp_solo: { label: 'PvP a solo' }, pvp_group: { label: 'PvP em grupo' }, pvp_instanced: { label: 'PvP instanciado', description: 'Batalhas competitivas estruturadas.' }, fast: { label: 'Rápido' }, heavy: { label: 'Pesado' }, siege: { label: 'Cerco' }, imperial: { label: 'Navio imperial' } } }, guides: { groups: { start: 'Primeiros passos' }, showAll: 'Mostrar todos os guias' }, specialists: { regularCount: '{count}/{max} espaços regulares' } } },
  ru: { discovery: { reset: 'Сбросить', results: 'Результаты', builds: { selectionCount: 'Выбрано {count}/{max}', tags: { pve_solo: { label: 'PvE в одиночку' }, pve_group: { label: 'PvE в группе' }, pve_instanced: { label: 'PvE-сценарий' }, pvp_solo: { label: 'PvP в одиночку' }, pvp_group: { label: 'PvP в группе' }, pvp_instanced: { label: 'PvP-сценарий', description: 'Структурированные соревновательные сражения.' }, fast: { label: 'Быстрый' }, heavy: { label: 'Тяжёлый' }, siege: { label: 'Осадный' }, imperial: { label: 'Имперский' } } }, guides: { groups: { start: 'Первые шаги' } }, specialists: { regularCount: '{count}/{max} обычных мест' } } },
  cn: { discovery: { reset: '重置', results: '结果', builds: { selectionCount: '已选择 {count}/{max}', tags: { pve_solo: { label: '单人 PvE' }, pve_group: { label: '组队 PvE' }, pve_instanced: { label: '副本 PvE' }, pvp_solo: { label: '单人 PvP' }, pvp_group: { label: '组队 PvP' }, pvp_instanced: { label: '副本 PvP', description: '结构化竞技战斗。' }, fast: { label: '高速' }, heavy: { label: '重型' }, siege: { label: '攻城' }, imperial: { label: '帝国' } } }, guides: { groups: { start: '入门' } }, specialists: { regularCount: '{count}/{max} 个常规槽位' } } },
}

Object.assign(discoveryModulesMessages.fr.discovery.builds, {
  resultEyebrow: 'Résultat calculé', liveResult: 'Résultat en direct', configureTitle: 'Configurer le build',
})
Object.assign(discoveryModulesMessages.es.discovery.builds, {
  resultEyebrow: 'Resultado calculado', liveResult: 'Resultado en directo', configureTitle: 'Configurar el build',
})
Object.assign(discoveryModulesMessages.pt.discovery.builds, {
  resultEyebrow: 'Resultado calculado', liveResult: 'Resultado em direto', configureTitle: 'Configurar o build',
})
Object.assign(discoveryModulesMessages.ru.discovery.builds, {
  resultEyebrow: 'Расчётный результат', liveResult: 'Результат в реальном времени',
})
Object.assign(discoveryModulesMessages.cn.discovery.builds, {
  resultEyebrow: '计算结果', liveResult: '实时结果',
})

discoveryModulesMessages.fr.builds = { list: { title: 'Bibliothèque de builds' } }
discoveryModulesMessages.fr.guides = { list: { title: 'Bibliothèque de guides' } }
discoveryModulesMessages.es.builds = { list: { title: 'Biblioteca de builds' } }
discoveryModulesMessages.pt.builds = { list: { title: 'Biblioteca de builds' } }
discoveryModulesMessages.ru.builds = { list: { title: 'Библиотека сборок' } }
discoveryModulesMessages.cn.builds = { list: { title: '配装库' } }
