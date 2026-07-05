import { computed, reactive, readonly } from 'vue'

export const DEFAULT_LOCALE = 'en'

export const SUPPORTED_LOCALES = [
  { code: 'de', label: 'DE', htmlLang: 'de' },
  { code: 'en', label: 'EN', htmlLang: 'en' },
  { code: 'fr', label: 'FR', htmlLang: 'fr' },
  { code: 'es', label: 'ES', htmlLang: 'es' },
  { code: 'pt', label: 'PT', htmlLang: 'pt' },
  { code: 'ru', label: 'RU', htmlLang: 'ru' },
  { code: 'cn', label: 'CN', htmlLang: 'zh-CN' },
]

const messages = {
  en: {
    common: {
      projectName: 'WoSB Community Hub',
      home: 'Home',
      builds: 'Builds',
      back: 'Back',
      cancel: 'Cancel',
      empty: 'Empty',
      language: 'Language',
      rate: 'Rate',
      type: 'Type',
      crew: 'Crew',
      free: 'Free',
      upgrades: 'Upgrades',
      sailorMinimum: 'Sailor minimum',
      quantity: 'Quantity',
      slots: 'slots',
      mainNavigation: 'Main navigation',
      admin: 'Admin',
    },
    footer: { text: 'WoSB Community Hub MVP' },
    auth: {
      eyebrow: 'Admin access',
      title: 'Sign in',
      subtitle: 'Minimal session login for the first protected hub area.',
      username: 'Username',
      password: 'Password',
      login: 'Login',
      logout: 'Logout',
      signingIn: 'Signing in ...',
      loginError: 'Login failed.',
      seedHint: 'Seed admin: admin / admin123. Change this before production.',
    },
    admin: {
      eyebrow: 'Administration',
      title: 'Admin panel',
      subtitle: 'A compact control room for hub health checks and first content moderation tasks.',
      lockedTitle: 'Admin login required',
      lockedText: 'Please sign in with an admin account to open this panel.',
      tabsLabel: 'Admin sections',
      tabs: { status: 'Status', builds: 'Builds' },
      status: {
        title: 'System status',
        subtitle: 'Operational details that are useful for maintainers, not for the public home page.',
        cardLabel: 'API connection',
        loading: 'Checking API ...',
        loadingDetail: 'Waiting for a response from the backend.',
        online: 'API online',
        onlineDetail: 'The backend responded successfully.',
        detailWithStatus: 'Backend health endpoint responded with status: {status}.',
        offline: 'API offline',
        offlineDetail: 'The backend could not be reached from the frontend.',
      },
      builds: {
        title: 'Build management',
        subtitle: 'Review and remove saved builds while the Build Manager is still in prototype mode.',
        summaryOne: '1 build',
        summaryMany: '{count} builds',
        searchPlaceholder: 'Search by build name, ship or type ...',
        loading: 'Loading builds ...',
        loadError: 'Admin builds could not be loaded.',
        deleteError: 'Build could not be deleted.',
        empty: 'No builds found.',
        delete: 'Delete',
        confirmDelete: 'Delete this build?',
        deleteNow: 'Delete now',
      },
    },
    home: {
      eyebrow: 'WoSB Community Hub',
      title: 'Your starting point for WoSB community tools.',
      subtitle: 'Find practical tools for planning ships, sharing setups and organizing play with your crew. The hub starts with the Build Manager and will grow step by step.',
      info: 'Hub status moved to the admin panel',
      apiLoading: 'Checking API ...',
      apiConnected: 'API online',
      apiOffline: 'API offline',
      aboutEyebrow: 'Community tools',
      aboutTitle: 'Plan faster, compare easier, sail better',
      about: 'WoSB Community Hub brings focused tools into one place so players can prepare builds and later coordinate groups without digging through scattered notes.',
      aboutExtra: 'The first public area is the Build Manager. More modules will appear here once they are ready for everyday use.',
      showcase: {
        eyebrow: 'Explore',
        title: 'Available tools',
        subtitle: 'Start with the active module below. Future tools will be added as separate cards so the home page stays clear.',
        openModule: 'Open module',
        builds: {
          eyebrow: 'Available now',
          title: 'Build Manager',
          description: 'Create, browse and compare ship builds with seeded ships, equipment slots, crew sliders and inventory-style cargo rows.',
          metaShips: 'Seeded ships',
          metaDesigner: 'Build designer',
          metaInventory: 'Inventory slots',
        },
        nextModuleEyebrow: 'Planned',
        nextModuleTitle: 'Groups, profiles and fleet tools',
        nextModuleText: 'Additional modules will appear here when they are stable enough for the community.',
      },
    },
    builds: {
      types: {
        all: 'All types',
        balanced: 'Balanced',
        gunnery: 'Gunnery',
        boarding: 'Boarding',
        defensive: 'Defensive',
      },
      list: {
        title: 'Build Manager',
        subtitle: 'Minimal overview of saved ship builds.',
        summaryOne: '1 build found',
        summaryMany: '{count} builds found',
        info: '{summary} · Filter by build name, ship or build type.',
        searchPlaceholder: 'Search by build name, ship or build type ...',
        newBuild: 'New build',
        loading: 'Loading builds ...',
        loadError: 'Builds could not be loaded.',
        empty: 'No builds yet.',
        crew: 'Crew {current}/{max}',
        sailorMin: 'Sailor min. {value}',
        upgradeSummary: '{used}/5 upgrades',
        inventorySummary: '{ammo} ammo · {consumables}/3 consumables · {hold} hold',
        noSlots: 'No slots',
        ammunitionPreview: 'Ammunition: {items}',
        consumablesPreview: 'Consumables: {items}',
        holdPreview: 'Hold: {items}',
      },
      create: {
        title: 'New build',
        subtitle: 'Minimal designer for ship, crew and loadout.',
        buildName: 'Build name',
        buildNamePlaceholder: 'Build name',
        buildType: 'Build type',
        ship: 'Ship',
        selectShip: 'Select ship',
        stats: {
          rate: 'Rate {value}',
          type: '{value}',
          crew: 'Crew {value}',
          sailorMinimum: 'Sailor min. {value}',
          upgrades: '5 upgrades',
        },
        sections: {
          identity: 'Build name',
          ship: 'Ship',
          equipment: 'Sails, upgrades and lantern',
          crew: 'Crew',
          inventory: 'Ammunition, consumables, hold',
          details: 'Details',
        },
        equipment: {
          sail: 'Sail',
          upgrade: 'Upgrade {index}',
          lantern: 'Lantern',
        },
        crew: {
          sailors: 'Sailors',
          musketeers: 'Musketeers',
          soldiers: 'Soldiers',
          mercenaries: 'Mercenaries',
          total: 'Crew: {current} / {max}',
          free: 'Free: {value}',
          sailorMinimum: 'Sailor minimum: {value}',
          tooFewSailors: 'too few sailors',
          tooManyCrew: 'too many people on board',
        },
        inventory: {
          ammunition: 'Ammunition',
          consumables: 'Consumables',
          hold: 'Hold',
          slotCount: '{count} slot(s)',
          limitedSlotCount: '{count} / {max} slot(s)',
          ammunitionHint: 'Ammunition and payloads. Same items stack through quantity.',
          consumablesHint: 'Active utility items such as repair kits, extra sails, smoke or rations.',
          holdHint: 'Cargo resources and trade goods such as Wood, Iron, Fabric or Fresh Meat.',
          ammunitionAlt: 'Ammunition slot {index}',
          consumableAlt: 'Consumable slot {index}',
          holdAlt: 'Hold slot {index}',
        },
        detailsPlaceholder: 'Notes, playstyle, matchups ...',
        loadError: 'Data could not be loaded.',
        saveError: 'Build could not be saved.',
        save: 'Save build',
        saving: 'Saving ...',
      },
      detail: {
        loading: 'Loading build ...',
        loadError: 'Build could not be loaded.',
        ship: 'Ship',
        buildType: 'Build type',
        sail: 'Sail',
        lantern: 'Lantern',
        inventory: 'Inventory',
        inventorySummary: '{ammo} ammo · {consumables}/3 consumables · {hold} hold',
        crewDistribution: 'Crew distribution',
        upgrades: 'Upgrades',
        ammunition: 'Ammunition',
        consumables: 'Consumables',
        hold: 'Hold',
        details: 'Details',
        noDetails: 'No details saved.',
      },
    },
  },
  de: {
    common: {
      home: 'Start', builds: 'Builds', back: 'Zurück', cancel: 'Abbrechen', empty: 'Leer', language: 'Sprache', rate: 'Rate', type: 'Typ', crew: 'Crew', free: 'Frei', upgrades: 'Upgrades', sailorMinimum: 'Matrosenminimum', quantity: 'Anzahl', slots: 'Slots', mainNavigation: 'Hauptnavigation',
    },
    footer: { text: 'WoSB MVP-Grundlage' },
    home: {
      eyebrow: 'Community Hub',
      title: 'WoSB Community Hub',
      subtitle: 'Dein Einstiegspunkt für praktische WoSB-Community-Tools: Builds planen, Setups vergleichen und später Gruppen organisieren.',
      info: 'Hub-Status ins Admin-Panel verschoben.',
      aboutEyebrow: 'Community-Tools',
      aboutTitle: 'Schneller planen, leichter vergleichen, besser segeln',
      about: 'Der WoSB Community Hub bündelt nützliche Werkzeuge an einem Ort, damit Spieler Builds vorbereiten und später einfacher zusammenfinden können.',
      aboutExtra: 'Den Anfang macht der Build-Manager. Weitere Module erscheinen hier, sobald sie stabil genug für den Alltag sind.',
      apiLoading: 'lade API ...',
      apiConnected: 'API verbunden',
      apiOffline: 'API nicht erreichbar, lokale Fallback-Texte aktiv',
      showcase: {
        eyebrow: 'Entdecken',
        title: 'Verfügbare Tools',
        subtitle: 'Starte mit dem aktiven Modul. Neue Werkzeuge werden später als eigene Karten ergänzt, damit die Startseite übersichtlich bleibt.',
        openModule: 'Modul öffnen',
        builds: {
          eyebrow: 'Erstes Modul',
          title: 'Build-Manager',
          description: 'Schiffs-Builds erstellen und durchsuchen mit geseedeten Schiffen, Equipment-Slots, Crew-Reglern und inventarartigen Laderaum-Zeilen.',
          metaShips: 'Geseedete Schiffe',
          metaDesigner: 'Build-Designer',
          metaInventory: 'Inventar-Slots',
        },
        nextModuleEyebrow: 'Geplant',
        nextModuleTitle: 'Weitere Community-Tools',
        nextModuleText: 'Weitere Module erscheinen hier, sobald sie stabil genug für die Community sind.',
      },
    },
    builds: {
      types: { all: 'Alle Typen', balanced: 'Ausgewogen', gunnery: 'Geschützfokus', boarding: 'Enterfokus', defensive: 'Defensiv' },
      list: { title: 'Build-Manager', subtitle: 'Minimale Übersicht gespeicherter Schiffs-Builds.', summaryOne: '1 Build gefunden', summaryMany: '{count} Builds gefunden', info: '{summary} · Filter nach Buildname, Schiff oder Build-Typ.', searchPlaceholder: 'Nach Build, Schiff oder Build-Typ suchen ...', newBuild: 'Neuer Build', loading: 'Builds werden geladen ...', loadError: 'Builds konnten nicht geladen werden.', empty: 'Noch keine Builds vorhanden.', crew: 'Crew {current}/{max}', sailorMin: 'Matrosen min. {value}', upgradeSummary: '{used}/5 Upgrades', inventorySummary: '{ammo} Munition · {consumables}/3 Verbrauchsgüter · {hold} Laderaum', noSlots: 'Keine Slots', ammunitionPreview: 'Munition: {items}', consumablesPreview: 'Verbrauchsgüter: {items}', holdPreview: 'Laderaum: {items}' },
      create: { title: 'Neuer Build', subtitle: 'Minimaler Designer für Schiff, Crew und Ausrüstung.', buildName: 'Build-Name', buildNamePlaceholder: 'Build-Name', buildType: 'Build-Typ', ship: 'Schiff', selectShip: 'Schiff auswählen', stats: { rate: 'Rate {value}', type: '{value}', crew: 'Crew {value}', sailorMinimum: 'Matrosen min. {value}', upgrades: '5 Upgrades' }, sections: { identity: 'Build-Name', ship: 'Schiff', equipment: 'Segel, Upgrades und Laterne', crew: 'Crew', inventory: 'Munition, Verbrauchsgüter, Laderaum', details: 'Details' }, equipment: { sail: 'Segel', upgrade: 'Upgrade {index}', lantern: 'Laterne' }, crew: { sailors: 'Matrosen', musketeers: 'Musketiere', soldiers: 'Soldaten', mercenaries: 'Söldner', total: 'Crew: {current} / {max}', free: 'Frei: {value}', sailorMinimum: 'Matrosenminimum: {value}', tooFewSailors: 'zu wenige Matrosen', tooManyCrew: 'zu viele Personen an Bord' }, inventory: { ammunition: 'Munition', consumables: 'Verbrauchsgüter', hold: 'Laderaum', slotCount: '{count} Slot(s)', limitedSlotCount: '{count} / {max} Slot(s)', ammunitionHint: 'Munition und Nutzlasten. Gleiche Items stapeln über die Anzahl.', consumablesHint: 'Aktive Hilfsitems wie Reparaturen, Zusatzsegel, Rauch oder Rationen.', holdHint: 'Rohstoffe und Handelswaren wie Wood, Iron, Fabric oder Fresh Meat.', ammunitionAlt: 'Munitionsslot {index}', consumableAlt: 'Verbrauchsgüter-Slot {index}', holdAlt: 'Laderaumslot {index}' }, detailsPlaceholder: 'Notizen, Spielstil, Matchups ...', loadError: 'Daten konnten nicht geladen werden.', saveError: 'Build konnte nicht gespeichert werden.', save: 'Build speichern', saving: 'Speichert ...' },
      detail: { loading: 'Build wird geladen ...', loadError: 'Build konnte nicht geladen werden.', ship: 'Schiff', buildType: 'Build-Typ', sail: 'Segel', lantern: 'Laterne', inventory: 'Inventar', inventorySummary: '{ammo} Munition · {consumables}/3 Verbrauchsgüter · {hold} Laderaum', crewDistribution: 'Crew-Verteilung', upgrades: 'Upgrades', ammunition: 'Munition', consumables: 'Verbrauchsgüter', hold: 'Laderaum', details: 'Details', noDetails: 'Keine Details gespeichert.' },
    },
  },
  fr: {
    common: { home: 'Accueil', builds: 'Builds', back: 'Retour', cancel: 'Annuler', empty: 'Vide', language: 'Langue', rate: 'Rang', type: 'Type', crew: 'Équipage', free: 'Libre', upgrades: 'Améliorations', sailorMinimum: 'Minimum de marins', quantity: 'Quantité', slots: 'emplacements', mainNavigation: 'Navigation principale' },
    footer: { text: 'Base MVP WoSB' },
    home: {
      eyebrow: 'Community Hub',
      title: 'WoSB Community Hub',
      subtitle: 'Votre point de départ pour planifier des builds, comparer des configurations et organiser plus tard le jeu en groupe.',
      info: 'Le statut du hub a été déplacé dans le panneau admin.',
      aboutEyebrow: 'Outils communautaires',
      aboutTitle: 'Planifier plus vite, comparer plus simplement, mieux naviguer',
      about: 'WoSB Community Hub rassemble des outils utiles en un seul endroit pour préparer des builds et, plus tard, coordonner des groupes plus facilement.',
      aboutExtra: 'Le Build Manager ouvre la marche. D’autres modules apparaîtront ici lorsqu’ils seront prêts pour une utilisation quotidienne.',
      apiLoading: 'chargement de l’API ...',
      apiConnected: 'API connectée',
      apiOffline: 'API indisponible, textes locaux utilisés',
      showcase: {
        eyebrow: 'Explorer',
        title: 'Outils disponibles',
        subtitle: 'Commencez avec le module actif. Les futurs outils seront ajoutés sous forme de cartes séparées pour garder la page claire.',
        openModule: 'Ouvrir le module',
        builds: {
          eyebrow: 'Premier module',
          title: 'Build Manager',
          description: 'Créer et parcourir des builds de navires avec navires seedés, emplacements d’équipement, curseurs d’équipage et lignes d’inventaire.',
          metaShips: 'Navires seedés',
          metaDesigner: 'Designer de builds',
          metaInventory: 'Slots d’inventaire',
        },
        nextModuleEyebrow: 'Prévu',
        nextModuleTitle: 'Autres outils communautaires',
        nextModuleText: 'Les prochains modules apparaîtront ici lorsqu’ils seront suffisamment stables pour la communauté.',
      },
    },
    builds: {
      types: { all: 'Tous les types', balanced: 'Équilibré', gunnery: 'Artillerie', boarding: 'Abordage', defensive: 'Défensif' },
      list: { title: 'Gestionnaire de builds', subtitle: 'Vue minimale des builds de navires sauvegardés.', summaryOne: '1 build trouvé', summaryMany: '{count} builds trouvés', info: '{summary} · Filtrer par nom, navire ou type.', searchPlaceholder: 'Rechercher un build ou navire ...', newBuild: 'Nouveau build', loading: 'Chargement des builds ...', loadError: 'Impossible de charger les builds.', empty: 'Aucun build pour le moment.', crew: 'Équipage {current}/{max}', sailorMin: 'Marins min. {value}', upgradeSummary: '{used}/5 améliorations', inventorySummary: '{ammo} munitions · {consumables}/3 consommables · {hold} cale', noSlots: 'Aucun emplacement', ammunitionPreview: 'Munitions : {items}', consumablesPreview: 'Consommables : {items}', holdPreview: 'Cale : {items}' },
      create: { title: 'Nouveau build', subtitle: 'Designer minimal pour navire, équipage et équipement.', buildName: 'Nom du build', buildNamePlaceholder: 'Nom du build', buildType: 'Type de build', ship: 'Navire', selectShip: 'Sélectionner un navire', stats: { rate: 'Rang {value}', type: '{value}', crew: 'Équipage {value}', sailorMinimum: 'Marins min. {value}', upgrades: '5 améliorations' }, sections: { identity: 'Nom du build', ship: 'Navire', equipment: 'Voiles, améliorations et lanterne', crew: 'Équipage', inventory: 'Munitions, consommables, cale', details: 'Détails' }, equipment: { sail: 'Voile', upgrade: 'Amélioration {index}', lantern: 'Lanterne' }, crew: { sailors: 'Marins', musketeers: 'Mousquetaires', soldiers: 'Soldats', mercenaries: 'Mercenaires', total: 'Équipage : {current} / {max}', free: 'Libre : {value}', sailorMinimum: 'Minimum de marins : {value}', tooFewSailors: 'pas assez de marins', tooManyCrew: 'trop de monde à bord' }, inventory: { ammunition: 'Munitions', consumables: 'Consommables', hold: 'Cale', slotCount: '{count} emplacement(s)', limitedSlotCount: '{count} / {max} emplacement(s)', ammunitionHint: 'Munitions et charges. Les mêmes objets se cumulent via la quantité.', consumablesHint: 'Objets utilitaires actifs comme réparations, voiles supplémentaires, fumée ou rations.', holdHint: 'Ressources et marchandises comme Wood, Iron, Fabric ou Fresh Meat.', ammunitionAlt: 'Emplacement de munition {index}', consumableAlt: 'Emplacement de consommable {index}', holdAlt: 'Emplacement de cale {index}' }, detailsPlaceholder: 'Notes, style de jeu, matchups ...', loadError: 'Impossible de charger les données.', saveError: 'Impossible d’enregistrer le build.', save: 'Enregistrer le build', saving: 'Enregistrement ...' },
      detail: { loading: 'Chargement du build ...', loadError: 'Impossible de charger le build.', ship: 'Navire', buildType: 'Type de build', sail: 'Voile', lantern: 'Lanterne', inventory: 'Inventaire', inventorySummary: '{ammo} munitions · {consumables}/3 consommables · {hold} cale', crewDistribution: 'Répartition de l’équipage', upgrades: 'Améliorations', ammunition: 'Munitions', consumables: 'Consommables', hold: 'Cale', details: 'Détails', noDetails: 'Aucun détail enregistré.' },
    },
  },
  es: {
    common: { home: 'Inicio', builds: 'Builds', back: 'Volver', cancel: 'Cancelar', empty: 'Vacío', language: 'Idioma', rate: 'Clase', type: 'Tipo', crew: 'Tripulación', free: 'Libre', upgrades: 'Mejoras', sailorMinimum: 'Mínimo de marineros', quantity: 'Cantidad', slots: 'ranuras', mainNavigation: 'Navegación principal' },
    footer: { text: 'Base MVP WoSB' },
    home: {
      eyebrow: 'Community Hub',
      title: 'WoSB Community Hub',
      subtitle: 'Tu punto de partida para planificar builds, comparar configuraciones y, más adelante, organizar grupos.',
      info: 'El estado del hub se movió al panel de administración.',
      aboutEyebrow: 'Herramientas comunitarias',
      aboutTitle: 'Planifica más rápido, compara mejor y navega con ventaja',
      about: 'WoSB Community Hub reúne herramientas útiles en un solo lugar para preparar builds y, más adelante, coordinar grupos con menos fricción.',
      aboutExtra: 'El Build Manager es el primer módulo público. Nuevos módulos aparecerán aquí cuando estén listos para el uso diario.',
      apiLoading: 'cargando API ...',
      apiConnected: 'API conectada',
      apiOffline: 'API no disponible, usando textos locales',
      showcase: {
        eyebrow: 'Explorar',
        title: 'Herramientas disponibles',
        subtitle: 'Empieza con el módulo activo. Las futuras herramientas se añadirán como tarjetas separadas para mantener la página clara.',
        openModule: 'Abrir módulo',
        builds: {
          eyebrow: 'Primer módulo',
          title: 'Build Manager',
          description: 'Crea y explora builds de barcos con barcos seed, ranuras de equipo, sliders de tripulación e inventario por slots.',
          metaShips: 'Barcos seed',
          metaDesigner: 'Diseñador de builds',
          metaInventory: 'Slots de inventario',
        },
        nextModuleEyebrow: 'Planificado',
        nextModuleTitle: 'Más herramientas comunitarias',
        nextModuleText: 'Los próximos módulos aparecerán aquí cuando sean lo bastante estables para la comunidad.',
      },
    },
    builds: {
      types: { all: 'Todos los tipos', balanced: 'Equilibrado', gunnery: 'Artillería', boarding: 'Abordaje', defensive: 'Defensivo' },
      list: { title: 'Gestor de builds', subtitle: 'Vista mínima de builds de barcos guardados.', summaryOne: '1 build encontrado', summaryMany: '{count} builds encontrados', info: '{summary} · Filtrar por nombre, barco o tipo.', searchPlaceholder: 'Buscar build o barco ...', newBuild: 'Nuevo build', loading: 'Cargando builds ...', loadError: 'No se pudieron cargar los builds.', empty: 'Aún no hay builds.', crew: 'Tripulación {current}/{max}', sailorMin: 'Marineros mín. {value}', upgradeSummary: '{used}/5 mejoras', inventorySummary: '{ammo} munición · {consumables}/3 consumibles · {hold} bodega', noSlots: 'Sin ranuras', ammunitionPreview: 'Munición: {items}', consumablesPreview: 'Consumibles: {items}', holdPreview: 'Bodega: {items}' },
      create: { title: 'Nuevo build', subtitle: 'Diseñador mínimo para barco, tripulación y equipo.', buildName: 'Nombre del build', buildNamePlaceholder: 'Nombre del build', buildType: 'Tipo de build', ship: 'Barco', selectShip: 'Seleccionar barco', stats: { rate: 'Clase {value}', type: '{value}', crew: 'Tripulación {value}', sailorMinimum: 'Marineros mín. {value}', upgrades: '5 mejoras' }, sections: { identity: 'Nombre del build', ship: 'Barco', equipment: 'Velas, mejoras y linterna', crew: 'Tripulación', inventory: 'Munición, consumibles, bodega', details: 'Detalles' }, equipment: { sail: 'Vela', upgrade: 'Mejora {index}', lantern: 'Linterna' }, crew: { sailors: 'Marineros', musketeers: 'Mosqueteros', soldiers: 'Soldados', mercenaries: 'Mercenarios', total: 'Tripulación: {current} / {max}', free: 'Libre: {value}', sailorMinimum: 'Mínimo de marineros: {value}', tooFewSailors: 'muy pocos marineros', tooManyCrew: 'demasiada gente a bordo' }, inventory: { ammunition: 'Munición', consumables: 'Consumibles', hold: 'Bodega', slotCount: '{count} ranura(s)', limitedSlotCount: '{count} / {max} ranura(s)', ammunitionHint: 'Munición y cargas. Los mismos objetos se apilan por cantidad.', consumablesHint: 'Objetos activos como reparaciones, velas extra, humo o raciones.', holdHint: 'Recursos y mercancías como Wood, Iron, Fabric o Fresh Meat.', ammunitionAlt: 'Ranura de munición {index}', consumableAlt: 'Ranura de consumible {index}', holdAlt: 'Ranura de bodega {index}' }, detailsPlaceholder: 'Notas, estilo de juego, matchups ...', loadError: 'No se pudieron cargar los datos.', saveError: 'No se pudo guardar el build.', save: 'Guardar build', saving: 'Guardando ...' },
      detail: { loading: 'Cargando build ...', loadError: 'No se pudo cargar el build.', ship: 'Barco', buildType: 'Tipo de build', sail: 'Vela', lantern: 'Linterna', inventory: 'Inventario', inventorySummary: '{ammo} munición · {consumables}/3 consumibles · {hold} bodega', crewDistribution: 'Distribución de tripulación', upgrades: 'Mejoras', ammunition: 'Munición', consumables: 'Consumibles', hold: 'Bodega', details: 'Detalles', noDetails: 'No hay detalles guardados.' },
    },
  },
  pt: {
    common: { home: 'Início', builds: 'Builds', back: 'Voltar', cancel: 'Cancelar', empty: 'Vazio', language: 'Idioma', rate: 'Classe', type: 'Tipo', crew: 'Tripulação', free: 'Livre', upgrades: 'Upgrades', sailorMinimum: 'Mínimo de marinheiros', quantity: 'Quantidade', slots: 'slots', mainNavigation: 'Navegação principal' },
    footer: { text: 'Base MVP WoSB' },
    home: {
      eyebrow: 'Community Hub',
      title: 'WoSB Community Hub',
      subtitle: 'Seu ponto de partida para planejar builds, comparar configurações e, depois, organizar grupos.',
      info: 'O status do hub foi movido para o painel admin.',
      aboutEyebrow: 'Base',
      aboutTitle: 'Planeje mais rápido, compare melhor e veleje com vantagem',
      about: 'O WoSB Community Hub reúne ferramentas úteis em um só lugar para preparar builds e, mais tarde, coordenar grupos com menos atrito.',
      aboutExtra: 'O Build Manager é o primeiro módulo público. Novos módulos aparecerão aqui quando estiverem prontos para o uso diário.',
      apiLoading: 'carregando API ...',
      apiConnected: 'API conectada',
      apiOffline: 'API indisponível, usando textos locais',
      showcase: {
        eyebrow: 'Explorar',
        title: 'Ferramentas disponíveis',
        subtitle: 'Comece pelo módulo ativo. Ferramentas futuras serão adicionadas como cartões separados para manter a página limpa.',
        openModule: 'Abrir módulo',
        builds: {
          eyebrow: 'Primeiro módulo',
          title: 'Build Manager',
          description: 'Crie e navegue por builds de navios com navios seedados, slots de equipamento, sliders de tripulação e inventário em slots.',
          metaShips: 'Navios seedados',
          metaDesigner: 'Designer de builds',
          metaInventory: 'Slots de inventário',
        },
        nextModuleEyebrow: 'Planejado',
        nextModuleTitle: 'Mais ferramentas da comunidade',
        nextModuleText: 'Os próximos módulos aparecerão aqui quando estiverem estáveis o suficiente para a comunidade.',
      },
    },
    builds: {
      types: { all: 'Todos os tipos', balanced: 'Equilibrado', gunnery: 'Artilharia', boarding: 'Abordagem', defensive: 'Defensivo' },
      list: { title: 'Gerenciador de builds', subtitle: 'Visão mínima dos builds de navios salvos.', summaryOne: '1 build encontrado', summaryMany: '{count} builds encontrados', info: '{summary} · Filtre por build, navio ou tipo.', searchPlaceholder: 'Buscar build ou navio ...', newBuild: 'Novo build', loading: 'Carregando builds ...', loadError: 'Não foi possível carregar os builds.', empty: 'Ainda não há builds.', crew: 'Tripulação {current}/{max}', sailorMin: 'Marinheiros mín. {value}', upgradeSummary: '{used}/5 upgrades', inventorySummary: '{ammo} munição · {consumables}/3 consumíveis · {hold} porão', noSlots: 'Sem slots', ammunitionPreview: 'Munição: {items}', consumablesPreview: 'Consumíveis: {items}', holdPreview: 'Porão: {items}' },
      create: { title: 'Novo build', subtitle: 'Designer mínimo para navio, tripulação e loadout.', buildName: 'Nome do build', buildNamePlaceholder: 'Nome do build', buildType: 'Tipo de build', ship: 'Navio', selectShip: 'Selecionar navio', stats: { rate: 'Classe {value}', type: '{value}', crew: 'Tripulação {value}', sailorMinimum: 'Marinheiros mín. {value}', upgrades: '5 upgrades' }, sections: { identity: 'Nome do build', ship: 'Navio', equipment: 'Velas, upgrades e lanterna', crew: 'Tripulação', inventory: 'Munição, consumíveis, porão', details: 'Detalhes' }, equipment: { sail: 'Vela', upgrade: 'Upgrade {index}', lantern: 'Lanterna' }, crew: { sailors: 'Marinheiros', musketeers: 'Mosqueteiros', soldiers: 'Soldados', mercenaries: 'Mercenários', total: 'Tripulação: {current} / {max}', free: 'Livre: {value}', sailorMinimum: 'Mínimo de marinheiros: {value}', tooFewSailors: 'poucos marinheiros', tooManyCrew: 'tripulação demais a bordo' }, inventory: { ammunition: 'Munição', consumables: 'Consumíveis', hold: 'Porão', slotCount: '{count} slot(s)', limitedSlotCount: '{count} / {max} slot(s)', ammunitionHint: 'Munição e cargas. Itens iguais acumulam pela quantidade.', consumablesHint: 'Utilitários ativos como kits, velas extras, fumaça ou rações.', holdHint: 'Recursos e mercadorias como Wood, Iron, Fabric ou Fresh Meat.', ammunitionAlt: 'Slot de munição {index}', consumableAlt: 'Slot de consumível {index}', holdAlt: 'Slot de porão {index}' }, detailsPlaceholder: 'Notas, estilo de jogo, matchups ...', loadError: 'Não foi possível carregar os dados.', saveError: 'Não foi possível salvar o build.', save: 'Salvar build', saving: 'Salvando ...' },
      detail: { loading: 'Carregando build ...', loadError: 'Não foi possível carregar o build.', ship: 'Navio', buildType: 'Tipo de build', sail: 'Vela', lantern: 'Lanterna', inventory: 'Inventário', inventorySummary: '{ammo} munição · {consumables}/3 consumíveis · {hold} porão', crewDistribution: 'Distribuição da tripulação', upgrades: 'Upgrades', ammunition: 'Munição', consumables: 'Consumíveis', hold: 'Porão', details: 'Detalhes', noDetails: 'Nenhum detalhe salvo.' },
    },
  },
  ru: {
    common: { home: 'Главная', builds: 'Билды', back: 'Назад', cancel: 'Отмена', empty: 'Пусто', language: 'Язык', rate: 'Ранг', type: 'Тип', crew: 'Команда', free: 'Свободно', upgrades: 'Улучшения', sailorMinimum: 'Минимум матросов', quantity: 'Количество', slots: 'слоты', mainNavigation: 'Главная навигация' },
    footer: { text: 'База MVP WoSB' },
    home: {
      eyebrow: 'Community Hub',
      title: 'WoSB Community Hub',
      subtitle: 'Стартовая точка для планирования билдов, сравнения наборов и будущей организации групп.',
      info: 'Статус хаба перенесён в админ-панель.',
      aboutEyebrow: 'Инструменты сообщества',
      aboutTitle: 'Планируйте быстрее, сравнивайте проще, выходите в море увереннее',
      about: 'WoSB Community Hub собирает полезные инструменты в одном месте: сначала для билдов, позже для групп и других задач сообщества.',
      aboutExtra: 'Build Manager — первый публичный модуль. Новые разделы появятся здесь, когда будут готовы для повседневного использования.',
      apiLoading: 'загрузка API ...',
      apiConnected: 'API подключено',
      apiOffline: 'API недоступно, используются локальные тексты',
      showcase: {
        eyebrow: 'Обзор',
        title: 'Доступные инструменты',
        subtitle: 'Начните с активного модуля. Будущие инструменты будут добавляться отдельными карточками, чтобы страница оставалась понятной.',
        openModule: 'Открыть модуль',
        builds: {
          eyebrow: 'Первый модуль',
          title: 'Build Manager',
          description: 'Создавайте и просматривайте билды кораблей с посеянными кораблями, слотами снаряжения, ползунками экипажа и инвентарными рядами.',
          metaShips: 'Корабли в seed',
          metaDesigner: 'Дизайнер билдов',
          metaInventory: 'Слоты инвентаря',
        },
        nextModuleEyebrow: 'В планах',
        nextModuleTitle: 'Другие инструменты сообщества',
        nextModuleText: 'Следующие модули появятся здесь, когда станут достаточно стабильными для сообщества.',
      },
    },
    builds: {
      types: { all: 'Все типы', balanced: 'Сбалансированный', gunnery: 'Артиллерия', boarding: 'Абордаж', defensive: 'Защита' },
      list: { title: 'Менеджер билдов', subtitle: 'Минимальный обзор сохранённых билдов кораблей.', summaryOne: 'Найден 1 билд', summaryMany: 'Найдено билдов: {count}', info: '{summary} · Фильтр по билду, кораблю или типу.', searchPlaceholder: 'Поиск билда или корабля ...', newBuild: 'Новый билд', loading: 'Загрузка билдов ...', loadError: 'Не удалось загрузить билды.', empty: 'Билдов пока нет.', crew: 'Команда {current}/{max}', sailorMin: 'Мин. матросов {value}', upgradeSummary: '{used}/5 улучшений', inventorySummary: '{ammo} боепр. · {consumables}/3 расходн. · {hold} трюм', noSlots: 'Нет слотов', ammunitionPreview: 'Боеприпасы: {items}', consumablesPreview: 'Расходники: {items}', holdPreview: 'Трюм: {items}' },
      create: { title: 'Новый билд', subtitle: 'Минимальный дизайнер корабля, команды и снаряжения.', buildName: 'Название билда', buildNamePlaceholder: 'Название билда', buildType: 'Тип билда', ship: 'Корабль', selectShip: 'Выберите корабль', stats: { rate: 'Ранг {value}', type: '{value}', crew: 'Команда {value}', sailorMinimum: 'Мин. матросов {value}', upgrades: '5 улучшений' }, sections: { identity: 'Название билда', ship: 'Корабль', equipment: 'Паруса, улучшения и фонарь', crew: 'Команда', inventory: 'Боеприпасы, расходники, трюм', details: 'Детали' }, equipment: { sail: 'Парус', upgrade: 'Улучшение {index}', lantern: 'Фонарь' }, crew: { sailors: 'Матросы', musketeers: 'Мушкетёры', soldiers: 'Солдаты', mercenaries: 'Наёмники', total: 'Команда: {current} / {max}', free: 'Свободно: {value}', sailorMinimum: 'Минимум матросов: {value}', tooFewSailors: 'слишком мало матросов', tooManyCrew: 'слишком много людей на борту' }, inventory: { ammunition: 'Боеприпасы', consumables: 'Расходники', hold: 'Трюм', slotCount: '{count} слот(ов)', limitedSlotCount: '{count} / {max} слот(ов)', ammunitionHint: 'Боеприпасы и заряды. Одинаковые предметы складываются по количеству.', consumablesHint: 'Активные предметы: ремонты, паруса, дым или рационы.', holdHint: 'Ресурсы и товары, например Wood, Iron, Fabric или Fresh Meat.', ammunitionAlt: 'Слот боеприпасов {index}', consumableAlt: 'Слот расходника {index}', holdAlt: 'Слот трюма {index}' }, detailsPlaceholder: 'Заметки, стиль игры, матчапы ...', loadError: 'Не удалось загрузить данные.', saveError: 'Не удалось сохранить билд.', save: 'Сохранить билд', saving: 'Сохранение ...' },
      detail: { loading: 'Загрузка билда ...', loadError: 'Не удалось загрузить билд.', ship: 'Корабль', buildType: 'Тип билда', sail: 'Парус', lantern: 'Фонарь', inventory: 'Инвентарь', inventorySummary: '{ammo} боепр. · {consumables}/3 расходн. · {hold} трюм', crewDistribution: 'Распределение команды', upgrades: 'Улучшения', ammunition: 'Боеприпасы', consumables: 'Расходники', hold: 'Трюм', details: 'Детали', noDetails: 'Детали не сохранены.' },
    },
  },
  cn: {
    common: { home: '首页', builds: '配置', back: '返回', cancel: '取消', empty: '空', language: '语言', rate: '等级', type: '类型', crew: '船员', free: '空余', upgrades: '升级', sailorMinimum: '水手最低值', quantity: '数量', slots: '槽位', mainNavigation: '主导航' },
    footer: { text: 'WoSB MVP 基础' },
    home: {
      eyebrow: 'Community Hub',
      title: 'WoSB Community Hub',
      subtitle: '用于规划配置、比较方案，并在之后组织队伍的 WoSB 社区工具入口。',
      info: 'Hub 状态已移动到管理员面板。',
      aboutEyebrow: '社区工具',
      aboutTitle: '更快规划，更易比较，更好出航',
      about: 'WoSB Community Hub 将实用工具集中在一个地方：先支持 Build Manager，之后再扩展队伍、资料和舰队工具。',
      aboutExtra: 'Build Manager 是第一个公开模块。后续模块稳定后会继续出现在这里。',
      apiLoading: '正在加载 API ...',
      apiConnected: 'API 已连接',
      apiOffline: 'API 不可用，正在使用本地文本',
      showcase: {
        eyebrow: '探索',
        title: '可用工具',
        subtitle: '从当前模块开始。未来工具会以独立卡片加入，让首页保持清晰。',
        openModule: '打开模块',
        builds: {
          eyebrow: '第一个模块',
          title: 'Build Manager',
          description: '使用已 seed 的船只、装备槽、船员滑块和库存槽来创建与浏览舰船 build。',
          metaShips: '已 seed 船只',
          metaDesigner: 'Build 设计器',
          metaInventory: '库存槽',
        },
        nextModuleEyebrow: '计划中',
        nextModuleTitle: '更多社区工具',
        nextModuleText: '新的模块会在足够稳定后出现在这里。',
      },
    },
    builds: {
      types: { all: '全部类型', balanced: '均衡', gunnery: '炮术', boarding: '登船', defensive: '防御' },
      list: { title: '配置管理器', subtitle: '已保存船只配置的极简概览。', summaryOne: '找到 1 个配置', summaryMany: '找到 {count} 个配置', info: '{summary} · 按配置名、船只或类型筛选。', searchPlaceholder: '搜索配置或船只 ...', newBuild: '新建配置', loading: '正在加载配置 ...', loadError: '无法加载配置。', empty: '暂无配置。', crew: '船员 {current}/{max}', sailorMin: '水手最低 {value}', upgradeSummary: '{used}/5 升级', inventorySummary: '{ammo} 弹药 · {consumables}/3 消耗品 · {hold} 货舱', noSlots: '无槽位', ammunitionPreview: '弹药：{items}', consumablesPreview: '消耗品：{items}', holdPreview: '货舱：{items}' },
      create: { title: '新建配置', subtitle: '船只、船员和装备的极简设计器。', buildName: '配置名称', buildNamePlaceholder: '配置名称', buildType: '配置类型', ship: '船只', selectShip: '选择船只', stats: { rate: '等级 {value}', type: '{value}', crew: '船员 {value}', sailorMinimum: '水手最低 {value}', upgrades: '5 升级' }, sections: { identity: '配置名称', ship: '船只', equipment: '船帆、升级和灯笼', crew: '船员', inventory: '弹药、消耗品、货舱', details: '详情' }, equipment: { sail: '船帆', upgrade: '升级 {index}', lantern: '灯笼' }, crew: { sailors: '水手', musketeers: '火枪手', soldiers: '士兵', mercenaries: '佣兵', total: '船员：{current} / {max}', free: '空余：{value}', sailorMinimum: '水手最低值：{value}', tooFewSailors: '水手太少', tooManyCrew: '船员超载' }, inventory: { ammunition: '弹药', consumables: '消耗品', hold: '货舱', slotCount: '{count} 个槽位', limitedSlotCount: '{count} / {max} 个槽位', ammunitionHint: '弹药和载荷。同类物品通过数量堆叠。', consumablesHint: '主动道具，如维修、备用帆、烟雾或口粮。', holdHint: '资源和贸易品，如 Wood、Iron、Fabric 或 Fresh Meat。', ammunitionAlt: '弹药槽 {index}', consumableAlt: '消耗品槽 {index}', holdAlt: '货舱槽 {index}' }, detailsPlaceholder: '备注、玩法、对局 ...', loadError: '无法加载数据。', saveError: '无法保存配置。', save: '保存配置', saving: '正在保存 ...' },
      detail: { loading: '正在加载配置 ...', loadError: '无法加载配置。', ship: '船只', buildType: '配置类型', sail: '船帆', lantern: '灯笼', inventory: '库存', inventorySummary: '{ammo} 弹药 · {consumables}/3 消耗品 · {hold} 货舱', crewDistribution: '船员分配', upgrades: '升级', ammunition: '弹药', consumables: '消耗品', hold: '货舱', details: '详情', noDetails: '未保存详情。' },
    },
  },
}

const optionTermGlossaries = {
  de: {
    'Ammunition Cradles': 'Munitionswiegen', 'Cellars': 'Keller', 'Double Hold': 'Doppelter Laderaum', 'Emergency Powder Charge': 'Notfall-Pulverladung', 'Extra Bunks': 'Zusätzliche Kojen', 'Fortified Gun Ports': 'Verstärkte Geschützpforten', 'Fortified Ports': 'Verstärkte Pforten', 'Incendiary Mixture': 'Brandmischung', 'Iron Ram': 'Eisenramme', 'Lightweight Hull': 'Leichter Rumpf', 'Long-Range Mortars': 'Langstrecken-Mörser', 'Reinforced Masts': 'Verstärkte Masten', 'Repair Arsenal': 'Reparaturarsenal', 'Structural Expansion': 'Strukturerweiterung', 'Strong Beams': 'Starke Balken', 'Sturdy Frames': 'Robuste Spanten', 'Swivel Mortars': 'Schwenkmörser', 'Teak Frames': 'Teakspanten',
    'Elite Sails': 'Elite-Segel', 'Imported Sails': 'Importierte Segel', 'Raiding Sails': 'Überfallsegel', 'Tarpaulin Sails': 'Plane-Segel', 'Golden Lantern': 'Goldene Laterne', 'Ice Lantern': 'Eislaterne', 'Red Lantern': 'Rote Laterne', 'Storm Lantern': 'Sturmlaterne',
    'Bar Shots': 'Stangenschüsse', 'Burning Arrows': 'Brennende Pfeile', 'Fire Ship': 'Brandschiff', 'Grapeshot': 'Kartätschen', 'Heated Shots': 'Glühende Kugeln', 'Large Phosphorous Mine': 'Große Phosphormine', 'Large Shrapnel Mines': 'Große Schrapnellminen', 'Phosphorous Shots': 'Phosphorschüsse', 'Round Shots': 'Runde Kugeln', 'Shrapnel Rounds': 'Schrapnellgeschosse', 'Small Flaming Barrels': 'Kleine Brandfässer', 'Small Gunpowder Barrels': 'Kleine Schießpulverfässer', 'Small Phosphorous Barrels': 'Kleine Phosphorfässer', 'Strike Rounds': 'Treffergeschosse',
    'Repair Kit': 'Reparaturset', 'Patches': 'Flicken', 'Additional Sails': 'Zusatzsegel', 'Double Powder': 'Doppelpulver', 'Signal Flare': 'Signalrakete', 'Ration': 'Ration', 'Smoke Bomb': 'Rauchbombe', 'Smoke Screen': 'Rauchwand', 'Bribery': 'Bestechung', 'Field Kit': 'Feldset', 'Horn': 'Horn', 'Powder Charge': 'Pulverladung', 'Poseidon\'s Hook': 'Poseidons Haken',
    'Animals': 'Tiere', 'Beam': 'Balken', 'Beer': 'Bier', 'Bulkhead': 'Schott', 'Canvas': 'Segeltuch', 'Chest': 'Kiste', 'Coal': 'Kohle', 'Copper Ore': 'Kupfererz', 'Dates': 'Datteln', 'Fabric': 'Stoff', 'Fresh Meat': 'Frischfleisch', 'Grain': 'Getreide', 'Iron Ore': 'Eisenerz', 'Leather': 'Leder', 'Nuts': 'Nüsse', 'Oil': 'Öl', 'Pineapples': 'Ananas', 'Provision': 'Proviant', 'Resin': 'Harz', 'Rugs': 'Teppiche', 'Salt': 'Salz', 'Silk': 'Seide', 'Supplies': 'Vorräte', 'Tobacco': 'Tabak', 'Water': 'Wasser', 'Whale Oil': 'Walöl', 'Wine': 'Wein', 'Wood': 'Holz', 'Wreckage': 'Wrackteile',
  },
  fr: {
    'Ammunition Cradles': 'Berceaux de munitions', 'Cellars': 'Celliers', 'Double Hold': 'Double cale', 'Emergency Powder Charge': 'Charge de poudre d’urgence', 'Extra Bunks': 'Couchettes supplémentaires', 'Fortified Gun Ports': 'Sabords renforcés', 'Fortified Ports': 'Sabords fortifiés', 'Incendiary Mixture': 'Mélange incendiaire', 'Iron Ram': 'Éperon de fer', 'Lightweight Hull': 'Coque légère', 'Long-Range Mortars': 'Mortiers longue portée', 'Reinforced Masts': 'Mâts renforcés', 'Repair Arsenal': 'Arsenal de réparation', 'Structural Expansion': 'Extension structurelle', 'Strong Beams': 'Poutres solides', 'Sturdy Frames': 'Membrures robustes', 'Swivel Mortars': 'Mortiers pivotants', 'Teak Frames': 'Membrures en teck',
    'Elite Sails': 'Voiles d’élite', 'Imported Sails': 'Voiles importées', 'Raiding Sails': 'Voiles de raid', 'Tarpaulin Sails': 'Voiles bâchées', 'Golden Lantern': 'Lanterne dorée', 'Ice Lantern': 'Lanterne de glace', 'Red Lantern': 'Lanterne rouge', 'Storm Lantern': 'Lanterne tempête',
    'Bar Shots': 'Boulets ramés', 'Burning Arrows': 'Flèches enflammées', 'Fire Ship': 'Brûlot', 'Grapeshot': 'Mitraille', 'Heated Shots': 'Boulets chauffés', 'Large Phosphorous Mine': 'Grande mine au phosphore', 'Large Shrapnel Mines': 'Grandes mines à shrapnels', 'Phosphorous Shots': 'Boulets au phosphore', 'Round Shots': 'Boulets ronds', 'Shrapnel Rounds': 'Obus à shrapnels', 'Small Flaming Barrels': 'Petits tonneaux incendiaires', 'Small Gunpowder Barrels': 'Petits tonneaux de poudre', 'Small Phosphorous Barrels': 'Petits tonneaux au phosphore', 'Strike Rounds': 'Projectiles de frappe',
    'Repair Kit': 'Kit de réparation', 'Patches': 'Rustines', 'Additional Sails': 'Voiles supplémentaires', 'Double Powder': 'Double poudre', 'Signal Flare': 'Fusée de signalisation', 'Ration': 'Ration', 'Smoke Bomb': 'Bombe fumigène', 'Smoke Screen': 'Écran de fumée', 'Bribery': 'Pot-de-vin', 'Field Kit': 'Kit de terrain', 'Horn': 'Corne', 'Powder Charge': 'Charge de poudre', 'Poseidon\'s Hook': 'Crochet de Poséidon',
    'Animals': 'Animaux', 'Beam': 'Poutre', 'Beer': 'Bière', 'Bulkhead': 'Cloison', 'Canvas': 'Toile', 'Chest': 'Coffre', 'Coal': 'Charbon', 'Copper Ore': 'Minerai de cuivre', 'Dates': 'Dattes', 'Fabric': 'Tissu', 'Fresh Meat': 'Viande fraîche', 'Grain': 'Grain', 'Iron Ore': 'Minerai de fer', 'Leather': 'Cuir', 'Nuts': 'Noix', 'Oil': 'Huile', 'Pineapples': 'Ananas', 'Provision': 'Provisions', 'Resin': 'Résine', 'Rugs': 'Tapis', 'Salt': 'Sel', 'Silk': 'Soie', 'Supplies': 'Ravitaillement', 'Tobacco': 'Tabac', 'Water': 'Eau', 'Whale Oil': 'Huile de baleine', 'Wine': 'Vin', 'Wood': 'Bois', 'Wreckage': 'Débris',
  },
  es: {
    'Ammunition Cradles': 'Soportes de munición', 'Cellars': 'Bodegas inferiores', 'Double Hold': 'Doble bodega', 'Emergency Powder Charge': 'Carga de pólvora de emergencia', 'Extra Bunks': 'Literas extra', 'Fortified Gun Ports': 'Portas reforzadas', 'Fortified Ports': 'Portas fortificadas', 'Incendiary Mixture': 'Mezcla incendiaria', 'Iron Ram': 'Espolón de hierro', 'Lightweight Hull': 'Casco ligero', 'Long-Range Mortars': 'Morteros de largo alcance', 'Reinforced Masts': 'Mástiles reforzados', 'Repair Arsenal': 'Arsenal de reparación', 'Structural Expansion': 'Expansión estructural', 'Strong Beams': 'Vigas fuertes', 'Sturdy Frames': 'Cuadernas robustas', 'Swivel Mortars': 'Morteros giratorios', 'Teak Frames': 'Cuadernas de teca',
    'Elite Sails': 'Velas de élite', 'Imported Sails': 'Velas importadas', 'Raiding Sails': 'Velas de incursión', 'Tarpaulin Sails': 'Velas de lona', 'Golden Lantern': 'Linterna dorada', 'Ice Lantern': 'Linterna de hielo', 'Red Lantern': 'Linterna roja', 'Storm Lantern': 'Linterna de tormenta',
    'Bar Shots': 'Tiros de barra', 'Burning Arrows': 'Flechas ardientes', 'Fire Ship': 'Brulote', 'Grapeshot': 'Metralla', 'Heated Shots': 'Tiros al rojo vivo', 'Large Phosphorous Mine': 'Mina grande de fósforo', 'Large Shrapnel Mines': 'Minas grandes de metralla', 'Phosphorous Shots': 'Tiros de fósforo', 'Round Shots': 'Balas redondas', 'Shrapnel Rounds': 'Proyectiles de metralla', 'Small Flaming Barrels': 'Barriles incendiarios pequeños', 'Small Gunpowder Barrels': 'Barriles pequeños de pólvora', 'Small Phosphorous Barrels': 'Barriles pequeños de fósforo', 'Strike Rounds': 'Proyectiles de impacto',
    'Repair Kit': 'Kit de reparación', 'Patches': 'Parches', 'Additional Sails': 'Velas adicionales', 'Double Powder': 'Pólvora doble', 'Signal Flare': 'Bengala de señal', 'Ration': 'Ración', 'Smoke Bomb': 'Bomba de humo', 'Smoke Screen': 'Pantalla de humo', 'Bribery': 'Soborno', 'Field Kit': 'Kit de campo', 'Horn': 'Cuerno', 'Powder Charge': 'Carga de pólvora', 'Poseidon\'s Hook': 'Gancho de Poseidón',
    'Animals': 'Animales', 'Beam': 'Viga', 'Beer': 'Cerveza', 'Bulkhead': 'Mamparo', 'Canvas': 'Lona', 'Chest': 'Cofre', 'Coal': 'Carbón', 'Copper Ore': 'Mineral de cobre', 'Dates': 'Dátiles', 'Fabric': 'Tela', 'Fresh Meat': 'Carne fresca', 'Grain': 'Grano', 'Iron Ore': 'Mineral de hierro', 'Leather': 'Cuero', 'Nuts': 'Nueces', 'Oil': 'Aceite', 'Pineapples': 'Piñas', 'Provision': 'Provisiones', 'Resin': 'Resina', 'Rugs': 'Alfombras', 'Salt': 'Sal', 'Silk': 'Seda', 'Supplies': 'Suministros', 'Tobacco': 'Tabaco', 'Water': 'Agua', 'Whale Oil': 'Aceite de ballena', 'Wine': 'Vino', 'Wood': 'Madera', 'Wreckage': 'Restos',
  },
  pt: {
    'Ammunition Cradles': 'Suportes de munição', 'Cellars': 'Porões inferiores', 'Double Hold': 'Porão duplo', 'Emergency Powder Charge': 'Carga de pólvora de emergência', 'Extra Bunks': 'Beliches extras', 'Fortified Gun Ports': 'Portinholas reforçadas', 'Fortified Ports': 'Portas fortificadas', 'Incendiary Mixture': 'Mistura incendiária', 'Iron Ram': 'Aríete de ferro', 'Lightweight Hull': 'Casco leve', 'Long-Range Mortars': 'Morteiros de longo alcance', 'Reinforced Masts': 'Mastros reforçados', 'Repair Arsenal': 'Arsenal de reparo', 'Structural Expansion': 'Expansão estrutural', 'Strong Beams': 'Vigas fortes', 'Sturdy Frames': 'Armações robustas', 'Swivel Mortars': 'Morteiros giratórios', 'Teak Frames': 'Armações de teca',
    'Elite Sails': 'Velas de elite', 'Imported Sails': 'Velas importadas', 'Raiding Sails': 'Velas de ataque', 'Tarpaulin Sails': 'Velas de lona', 'Golden Lantern': 'Lanterna dourada', 'Ice Lantern': 'Lanterna de gelo', 'Red Lantern': 'Lanterna vermelha', 'Storm Lantern': 'Lanterna de tempestade',
    'Bar Shots': 'Tiros de barra', 'Burning Arrows': 'Flechas flamejantes', 'Fire Ship': 'Navio incendiário', 'Grapeshot': 'Metralha', 'Heated Shots': 'Tiros aquecidos', 'Large Phosphorous Mine': 'Mina grande de fósforo', 'Large Shrapnel Mines': 'Minas grandes de estilhaços', 'Phosphorous Shots': 'Tiros de fósforo', 'Round Shots': 'Tiros redondos', 'Shrapnel Rounds': 'Projéteis de estilhaços', 'Small Flaming Barrels': 'Barris incendiários pequenos', 'Small Gunpowder Barrels': 'Barris pequenos de pólvora', 'Small Phosphorous Barrels': 'Barris pequenos de fósforo', 'Strike Rounds': 'Projéteis de impacto',
    'Repair Kit': 'Kit de reparo', 'Patches': 'Remendos', 'Additional Sails': 'Velas adicionais', 'Double Powder': 'Pólvora dupla', 'Signal Flare': 'Sinalizador', 'Ration': 'Ração', 'Smoke Bomb': 'Bomba de fumaça', 'Smoke Screen': 'Cortina de fumaça', 'Bribery': 'Suborno', 'Field Kit': 'Kit de campo', 'Horn': 'Chifre', 'Powder Charge': 'Carga de pólvora', 'Poseidon\'s Hook': 'Gancho de Poseidon',
    'Animals': 'Animais', 'Beam': 'Viga', 'Beer': 'Cerveja', 'Bulkhead': 'Antepara', 'Canvas': 'Lona', 'Chest': 'Baú', 'Coal': 'Carvão', 'Copper Ore': 'Minério de cobre', 'Dates': 'Tâmaras', 'Fabric': 'Tecido', 'Fresh Meat': 'Carne fresca', 'Grain': 'Grãos', 'Iron Ore': 'Minério de ferro', 'Leather': 'Couro', 'Nuts': 'Nozes', 'Oil': 'Óleo', 'Pineapples': 'Abacaxis', 'Provision': 'Provisões', 'Resin': 'Resina', 'Rugs': 'Tapetes', 'Salt': 'Sal', 'Silk': 'Seda', 'Supplies': 'Suprimentos', 'Tobacco': 'Tabaco', 'Water': 'Água', 'Whale Oil': 'Óleo de baleia', 'Wine': 'Vinho', 'Wood': 'Madeira', 'Wreckage': 'Destroços',
  },
  ru: {
    'Ammunition Cradles': 'Лотки для боеприпасов', 'Cellars': 'Погреба', 'Double Hold': 'Двойной трюм', 'Emergency Powder Charge': 'Аварийный пороховой заряд', 'Extra Bunks': 'Дополнительные койки', 'Fortified Gun Ports': 'Усиленные пушечные порты', 'Fortified Ports': 'Укреплённые порты', 'Incendiary Mixture': 'Зажигательная смесь', 'Iron Ram': 'Железный таран', 'Lightweight Hull': 'Облегчённый корпус', 'Long-Range Mortars': 'Дальнобойные мортиры', 'Reinforced Masts': 'Усиленные мачты', 'Repair Arsenal': 'Ремонтный арсенал', 'Structural Expansion': 'Структурное расширение', 'Strong Beams': 'Прочные балки', 'Sturdy Frames': 'Крепкие шпангоуты', 'Swivel Mortars': 'Поворотные мортиры', 'Teak Frames': 'Тиковые шпангоуты',
    'Elite Sails': 'Элитные паруса', 'Imported Sails': 'Импортные паруса', 'Raiding Sails': 'Рейдерские паруса', 'Tarpaulin Sails': 'Брезентовые паруса', 'Golden Lantern': 'Золотой фонарь', 'Ice Lantern': 'Ледяной фонарь', 'Red Lantern': 'Красный фонарь', 'Storm Lantern': 'Штормовой фонарь',
    'Bar Shots': 'Книппели', 'Burning Arrows': 'Горящие стрелы', 'Fire Ship': 'Брандер', 'Grapeshot': 'Картечь', 'Heated Shots': 'Калёные ядра', 'Large Phosphorous Mine': 'Большая фосфорная мина', 'Large Shrapnel Mines': 'Большие шрапнельные мины', 'Phosphorous Shots': 'Фосфорные ядра', 'Round Shots': 'Круглые ядра', 'Shrapnel Rounds': 'Шрапнельные снаряды', 'Small Flaming Barrels': 'Малые горящие бочки', 'Small Gunpowder Barrels': 'Малые пороховые бочки', 'Small Phosphorous Barrels': 'Малые фосфорные бочки', 'Strike Rounds': 'Ударные снаряды',
    'Repair Kit': 'Ремкомплект', 'Patches': 'Заплаты', 'Additional Sails': 'Дополнительные паруса', 'Double Powder': 'Двойной порох', 'Signal Flare': 'Сигнальная ракета', 'Ration': 'Рацион', 'Smoke Bomb': 'Дымовая бомба', 'Smoke Screen': 'Дымовая завеса', 'Bribery': 'Взятка', 'Field Kit': 'Полевой набор', 'Horn': 'Горн', 'Powder Charge': 'Пороховой заряд', 'Poseidon\'s Hook': 'Крюк Посейдона',
    'Animals': 'Животные', 'Beam': 'Балка', 'Beer': 'Пиво', 'Bulkhead': 'Переборка', 'Canvas': 'Парусина', 'Chest': 'Сундук', 'Coal': 'Уголь', 'Copper Ore': 'Медная руда', 'Dates': 'Финики', 'Fabric': 'Ткань', 'Fresh Meat': 'Свежее мясо', 'Grain': 'Зерно', 'Iron Ore': 'Железная руда', 'Leather': 'Кожа', 'Nuts': 'Орехи', 'Oil': 'Масло', 'Pineapples': 'Ананасы', 'Provision': 'Провизия', 'Resin': 'Смола', 'Rugs': 'Ковры', 'Salt': 'Соль', 'Silk': 'Шёлк', 'Supplies': 'Припасы', 'Tobacco': 'Табак', 'Water': 'Вода', 'Whale Oil': 'Китовый жир', 'Wine': 'Вино', 'Wood': 'Дерево', 'Wreckage': 'Обломки',
  },
  cn: {
    'Ammunition Cradles': '弹药托架', 'Cellars': '地窖', 'Double Hold': '双层货舱', 'Emergency Powder Charge': '应急火药装药', 'Extra Bunks': '额外床位', 'Fortified Gun Ports': '强化炮门', 'Fortified Ports': '加固炮门', 'Incendiary Mixture': '燃烧混合物', 'Iron Ram': '铁质撞角', 'Lightweight Hull': '轻量船体', 'Long-Range Mortars': '远程迫击炮', 'Reinforced Masts': '强化桅杆', 'Repair Arsenal': '维修军械库', 'Structural Expansion': '结构扩展', 'Strong Beams': '坚固横梁', 'Sturdy Frames': '坚固肋骨', 'Swivel Mortars': '旋转迫击炮', 'Teak Frames': '柚木肋骨',
    'Elite Sails': '精英船帆', 'Imported Sails': '进口船帆', 'Raiding Sails': '突袭船帆', 'Tarpaulin Sails': '篷布船帆', 'Golden Lantern': '金色灯笼', 'Ice Lantern': '冰灯笼', 'Red Lantern': '红灯笼', 'Storm Lantern': '风暴灯笼',
    'Bar Shots': '链杆弹', 'Burning Arrows': '燃烧箭', 'Fire Ship': '火船', 'Grapeshot': '霰弹', 'Heated Shots': '炽热炮弹', 'Large Phosphorous Mine': '大型磷矿雷', 'Large Shrapnel Mines': '大型破片雷', 'Phosphorous Shots': '磷炮弹', 'Round Shots': '圆炮弹', 'Shrapnel Rounds': '破片弹', 'Small Flaming Barrels': '小型燃烧桶', 'Small Gunpowder Barrels': '小型火药桶', 'Small Phosphorous Barrels': '小型磷桶', 'Strike Rounds': '冲击弹',
    'Repair Kit': '维修包', 'Patches': '补丁', 'Additional Sails': '备用帆', 'Double Powder': '双倍火药', 'Signal Flare': '信号弹', 'Ration': '口粮', 'Smoke Bomb': '烟雾弹', 'Smoke Screen': '烟幕', 'Bribery': '贿赂', 'Field Kit': '野战包', 'Horn': '号角', 'Powder Charge': '火药装药', 'Poseidon\'s Hook': '波塞冬之钩',
    'Animals': '动物', 'Beam': '横梁', 'Beer': '啤酒', 'Bulkhead': '隔舱板', 'Canvas': '帆布', 'Chest': '箱子', 'Coal': '煤炭', 'Copper Ore': '铜矿石', 'Dates': '椰枣', 'Fabric': '织物', 'Fresh Meat': '鲜肉', 'Grain': '谷物', 'Iron Ore': '铁矿石', 'Leather': '皮革', 'Nuts': '坚果', 'Oil': '油', 'Pineapples': '菠萝', 'Provision': '补给', 'Resin': '树脂', 'Rugs': '地毯', 'Salt': '盐', 'Silk': '丝绸', 'Supplies': '物资', 'Tobacco': '烟草', 'Water': '水', 'Whale Oil': '鲸油', 'Wine': '葡萄酒', 'Wood': '木材', 'Wreckage': '残骸',
  },
}


const authAdminProfileMessages = {
  en: {
    common: { profile: 'Profile', staffPanel: 'Staff panel', save: 'Save' },
    roles: { user: 'User', moderator: 'Moderator', admin: 'Admin' },
    auth: {
      register: 'Register',
      registerEyebrow: 'Join the hub',
      registerTitle: 'Create your account',
      registerSubtitle: 'Create a simple account for your profile and future community features.',
      createAccount: 'Create account',
      creatingAccount: 'Creating account ...',
      registerError: 'Registration failed.',
      registerSuccess: 'Account created. You can sign in now.',
      alreadyAccount: 'Already have an account?',
      noAccount: 'No account yet?',
    },
    admin: {
      moderatorTitle: 'Moderator panel',
      moderatorSubtitle: 'A compact moderation area for managing public builds.',
      tabs: { users: 'Moderators' },
      users: {
        title: 'Moderators',
        subtitle: 'Create moderator accounts and review the current users. Moderators can use this panel, but cannot create other moderators.',
        summaryOne: '1 user',
        summaryMany: '{count} users',
        createModerator: 'Create moderator',
        createModeratorError: 'Moderator could not be created.',
        moderatorCreated: 'Moderator created.',
        loading: 'Loading users ...',
        loadError: 'Users could not be loaded.',
      },
    },
    profile: {
      eyebrow: 'Account',
      title: 'Your profile',
      subtitle: 'Keep your public WoSB profile compact and useful for later modules.',
      loading: 'Loading profile ...',
      account: 'Account',
      displayName: 'Display name',
      fleetName: 'Fleet',
      fleetPlaceholder: 'Optional fleet name',
      preferredFocus: 'Preferred focus',
      noPreferredFocus: 'No preferred focus',
      note: 'Profile note',
      notePlaceholder: 'Optional short note for later group and community tools.',
      save: 'Save profile',
      saving: 'Saving ...',
      saved: 'Profile saved.',
      loadError: 'Profile could not be loaded.',
      saveError: 'Profile could not be saved.',
    },
    focus: {
      pve_farming: 'PvE Farming',
      pve_imp_hunting: 'PvE Imp Hunting',
      pve_general: 'PvE General',
      pvp_open_world: 'PvP Open World',
      pvp_arena: 'PvP Arena',
      pvp_general: 'PvP General',
      trading: 'Trading',
      other: 'Other',
    },
  },
  de: {
    common: { profile: 'Profil', staffPanel: 'Team-Panel', save: 'Speichern' },
    roles: { user: 'Nutzer', moderator: 'Moderator', admin: 'Admin' },
    auth: {
      register: 'Registrieren', registerEyebrow: 'Dem Hub beitreten', registerTitle: 'Account erstellen',
      registerSubtitle: 'Erstelle einen einfachen Account für dein Profil und spätere Community-Funktionen.',
      createAccount: 'Account erstellen', creatingAccount: 'Account wird erstellt ...', registerError: 'Registrierung fehlgeschlagen.',
      registerSuccess: 'Account erstellt. Du kannst dich jetzt anmelden.', alreadyAccount: 'Du hast schon einen Account?', noAccount: 'Noch keinen Account?',
    },
    admin: {
      moderatorTitle: 'Moderations-Panel', moderatorSubtitle: 'Ein kompaktes Moderationspanel zur Verwaltung öffentlicher Builds.',
      tabs: { users: 'Moderatoren' },
      users: {
        title: 'Moderatoren', subtitle: 'Erstelle Moderator-Accounts und prüfe aktuelle Nutzer. Moderatoren können dieses Panel nutzen, aber keine weiteren Moderatoren erstellen.',
        summaryOne: '1 Nutzer', summaryMany: '{count} Nutzer', createModerator: 'Moderator erstellen', createModeratorError: 'Moderator konnte nicht erstellt werden.',
        moderatorCreated: 'Moderator erstellt.', loading: 'Nutzer werden geladen ...', loadError: 'Nutzer konnten nicht geladen werden.',
      },
    },
    profile: {
      eyebrow: 'Account', title: 'Dein Profil', subtitle: 'Halte dein öffentliches WoSB-Profil kompakt und nützlich für spätere Module.',
      loading: 'Profil wird geladen ...', account: 'Account', displayName: 'Anzeigename', fleetName: 'Flotte', fleetPlaceholder: 'Optionale Flotte',
      preferredFocus: 'Bevorzugter Fokus', noPreferredFocus: 'Kein bevorzugter Fokus', note: 'Profilnotiz', notePlaceholder: 'Optionale kurze Notiz für spätere Gruppen- und Community-Tools.',
      save: 'Profil speichern', saving: 'Speichert ...', saved: 'Profil gespeichert.', loadError: 'Profil konnte nicht geladen werden.', saveError: 'Profil konnte nicht gespeichert werden.',
    },
    focus: {
      pve_farming: 'PvE Farming', pve_imp_hunting: 'PvE Imp-Hunting', pve_general: 'PvE Allgemein', pvp_open_world: 'PvP Open-World',
      pvp_arena: 'PvP Arena', pvp_general: 'PvP Allgemein', trading: 'Trading', other: 'Sonstiges',
    },
  },
  fr: {}, es: {}, pt: {}, ru: {}, cn: {},
}


const userBuildsAndPasswordMessages = {
  en: {
    auth: {
      loginEyebrow: 'Welcome back',
      loginTitle: 'Sign in to your hub account',
      loginSubtitle: 'Use one simple session login to manage your profile, your own builds and staff tools when available.',
      usernamePlaceholder: 'Your username',
      passwordPlaceholder: 'Your password',
      sessionHint: 'This MVP uses a secure HttpOnly session cookie, not JWT.',
      loginBenefitsLabel: 'Login benefits',
      loginBenefits: {
        profile: 'Profile settings',
        myBuilds: 'Your own builds',
        staff: 'Staff tools when assigned',
      },
    },
    myBuilds: {
      eyebrow: 'Build workspace',
      title: 'My builds',
      subtitle: 'Manage the builds you created yourself. Public builds remain visible in the Build Manager.',
      summaryOne: '1 own build',
      summaryMany: '{count} own builds',
      create: 'Create build',
      filtersLabel: 'Filter your builds',
      manageTitle: 'Your build library',
      manageText: 'Search by name, ship or build type and remove outdated personal builds when needed.',
      searchPlaceholder: 'Search your builds by name, ship or type ...',
      loading: 'Loading your builds ...',
      loadError: 'Your builds could not be loaded.',
      deleteError: 'Build could not be deleted.',
      emptyTitle: 'No own builds yet',
      emptyText: 'Create your first build to start building your personal library.',
      createFirst: 'Create first build',
      confirmDelete: 'Delete this build from your library?',
      delete: 'Delete',
      deleteNow: 'Delete now',
      open: 'Open my builds',
      profileCardTitle: 'My builds',
      profileCardText: 'A compact personal management area for builds you created. Think of it as a small admin panel for your own content.',
    },
    profile: {
      password: {
        eyebrow: 'Security',
        title: 'Change password',
        subtitle: 'Update your password without changing your profile data.',
        current: 'Current password',
        new: 'New password',
        repeat: 'Repeat new password',
        save: 'Update password',
        saving: 'Updating ...',
        changed: 'Password changed.',
        repeatMismatch: 'The new passwords do not match.',
        changeError: 'Password could not be changed.',
      },
    },
  },
  de: {
    auth: {
      loginEyebrow: 'Willkommen zurück',
      loginTitle: 'Melde dich im Hub an',
      loginSubtitle: 'Nutze einen einfachen Session-Login, um dein Profil, deine eigenen Builds und verfügbare Team-Werkzeuge zu verwalten.',
      usernamePlaceholder: 'Dein Benutzername',
      passwordPlaceholder: 'Dein Passwort',
      sessionHint: 'Dieses MVP nutzt ein sicheres HttpOnly-Session-Cookie, kein JWT.',
      loginBenefitsLabel: 'Login-Vorteile',
      loginBenefits: { profile: 'Profileinstellungen', myBuilds: 'Eigene Builds', staff: 'Team-Werkzeuge bei Freischaltung' },
    },
    myBuilds: {
      eyebrow: 'Build-Arbeitsbereich', title: 'Meine Builds', subtitle: 'Verwalte die Builds, die du selbst erstellt hast. Öffentliche Builds bleiben im Build-Manager sichtbar.',
      summaryOne: '1 eigener Build', summaryMany: '{count} eigene Builds', create: 'Build erstellen', filtersLabel: 'Eigene Builds filtern', manageTitle: 'Deine Build-Bibliothek',
      manageText: 'Suche nach Name, Schiff oder Build-Typ und entferne veraltete eigene Builds bei Bedarf.', searchPlaceholder: 'Eigene Builds nach Name, Schiff oder Typ suchen ...',
      loading: 'Eigene Builds werden geladen ...', loadError: 'Eigene Builds konnten nicht geladen werden.', deleteError: 'Build konnte nicht gelöscht werden.',
      emptyTitle: 'Noch keine eigenen Builds', emptyText: 'Erstelle deinen ersten Build, um deine persönliche Bibliothek aufzubauen.', createFirst: 'Ersten Build erstellen',
      confirmDelete: 'Diesen Build aus deiner Bibliothek löschen?', delete: 'Löschen', deleteNow: 'Jetzt löschen', open: 'Meine Builds öffnen', profileCardTitle: 'Meine Builds',
      profileCardText: 'Ein kompakter Verwaltungsbereich für Builds, die du selbst erstellt hast. Quasi ein kleines Admin-Panel für deine eigenen Inhalte.',
    },
    profile: { password: { eyebrow: 'Sicherheit', title: 'Passwort ändern', subtitle: 'Aktualisiere dein Passwort, ohne deine Profildaten zu ändern.', current: 'Aktuelles Passwort', new: 'Neues Passwort', repeat: 'Neues Passwort wiederholen', save: 'Passwort aktualisieren', saving: 'Aktualisiert ...', changed: 'Passwort geändert.', repeatMismatch: 'Die neuen Passwörter stimmen nicht überein.', changeError: 'Passwort konnte nicht geändert werden.' } },
  },
  fr: {
    auth: { loginEyebrow: 'Bon retour', loginTitle: 'Connectez-vous au hub', loginSubtitle: 'Utilisez une session simple pour gérer votre profil, vos builds et les outils staff disponibles.', usernamePlaceholder: 'Votre identifiant', passwordPlaceholder: 'Votre mot de passe', sessionHint: 'Ce MVP utilise un cookie de session HttpOnly sécurisé, pas de JWT.', loginBenefitsLabel: 'Avantages de connexion',
      loginBenefits: { profile: 'Paramètres du profil', myBuilds: 'Vos builds', staff: 'Outils staff si autorisés' } },
    myBuilds: { eyebrow: 'Espace builds', title: 'Mes builds', subtitle: 'Gérez les builds que vous avez créés. Les builds publics restent visibles dans le Build Manager.', summaryOne: '1 build personnel', summaryMany: '{count} builds personnels', create: 'Créer un build', filtersLabel: 'Filtrer vos builds', manageTitle: 'Votre bibliothèque de builds', manageText: 'Recherchez par nom, navire ou type et supprimez les builds personnels obsolètes.', searchPlaceholder: 'Rechercher vos builds par nom, navire ou type ...', loading: 'Chargement de vos builds ...', loadError: 'Impossible de charger vos builds.', deleteError: 'Impossible de supprimer le build.', emptyTitle: 'Aucun build personnel', emptyText: 'Créez votre premier build pour démarrer votre bibliothèque personnelle.', createFirst: 'Créer le premier build', confirmDelete: 'Supprimer ce build de votre bibliothèque ?', delete: 'Supprimer', deleteNow: 'Supprimer maintenant', open: 'Ouvrir mes builds', profileCardTitle: 'Mes builds', profileCardText: 'Un espace de gestion compact pour les builds que vous avez créés, comme un petit panneau admin pour vos contenus.' },
    profile: { password: { eyebrow: 'Sécurité', title: 'Changer le mot de passe', subtitle: 'Mettez à jour votre mot de passe sans modifier votre profil.', current: 'Mot de passe actuel', new: 'Nouveau mot de passe', repeat: 'Répéter le nouveau mot de passe', save: 'Mettre à jour', saving: 'Mise à jour ...', changed: 'Mot de passe changé.', repeatMismatch: 'Les nouveaux mots de passe ne correspondent pas.', changeError: 'Impossible de changer le mot de passe.' } },
  },
  es: {
    auth: { loginEyebrow: 'Bienvenido de nuevo', loginTitle: 'Inicia sesión en el hub', loginSubtitle: 'Usa una sesión simple para gestionar tu perfil, tus builds y herramientas de staff disponibles.', usernamePlaceholder: 'Tu usuario', passwordPlaceholder: 'Tu contraseña', sessionHint: 'Este MVP usa una cookie de sesión HttpOnly segura, no JWT.', loginBenefitsLabel: 'Ventajas del login',
      loginBenefits: { profile: 'Ajustes de perfil', myBuilds: 'Tus builds', staff: 'Herramientas de staff si están activas' } },
    myBuilds: { eyebrow: 'Área de builds', title: 'Mis builds', subtitle: 'Gestiona los builds que has creado. Los builds públicos siguen visibles en el Build Manager.', summaryOne: '1 build propio', summaryMany: '{count} builds propios', create: 'Crear build', filtersLabel: 'Filtrar tus builds', manageTitle: 'Tu biblioteca de builds', manageText: 'Busca por nombre, barco o tipo y elimina builds personales obsoletos.', searchPlaceholder: 'Buscar tus builds por nombre, barco o tipo ...', loading: 'Cargando tus builds ...', loadError: 'No se pudieron cargar tus builds.', deleteError: 'No se pudo eliminar el build.', emptyTitle: 'Aún no tienes builds', emptyText: 'Crea tu primer build para empezar tu biblioteca personal.', createFirst: 'Crear primer build', confirmDelete: '¿Eliminar este build de tu biblioteca?', delete: 'Eliminar', deleteNow: 'Eliminar ahora', open: 'Abrir mis builds', profileCardTitle: 'Mis builds', profileCardText: 'Un área compacta para gestionar los builds que has creado, como un pequeño panel admin para tu contenido.' },
    profile: { password: { eyebrow: 'Seguridad', title: 'Cambiar contraseña', subtitle: 'Actualiza tu contraseña sin cambiar tu perfil.', current: 'Contraseña actual', new: 'Nueva contraseña', repeat: 'Repetir nueva contraseña', save: 'Actualizar contraseña', saving: 'Actualizando ...', changed: 'Contraseña cambiada.', repeatMismatch: 'Las nuevas contraseñas no coinciden.', changeError: 'No se pudo cambiar la contraseña.' } },
  },
  pt: {
    auth: { loginEyebrow: 'Bem-vindo de volta', loginTitle: 'Entrar no hub', loginSubtitle: 'Use uma sessão simples para gerenciar seu perfil, seus builds e ferramentas de staff disponíveis.', usernamePlaceholder: 'Seu usuário', passwordPlaceholder: 'Sua senha', sessionHint: 'Este MVP usa um cookie de sessão HttpOnly seguro, não JWT.', loginBenefitsLabel: 'Benefícios do login',
      loginBenefits: { profile: 'Configurações de perfil', myBuilds: 'Seus builds', staff: 'Ferramentas de staff se liberadas' } },
    myBuilds: { eyebrow: 'Área de builds', title: 'Meus builds', subtitle: 'Gerencie os builds que você criou. Builds públicos continuam visíveis no Build Manager.', summaryOne: '1 build próprio', summaryMany: '{count} builds próprios', create: 'Criar build', filtersLabel: 'Filtrar seus builds', manageTitle: 'Sua biblioteca de builds', manageText: 'Pesquise por nome, navio ou tipo e remova builds pessoais antigos.', searchPlaceholder: 'Pesquisar seus builds por nome, navio ou tipo ...', loading: 'Carregando seus builds ...', loadError: 'Não foi possível carregar seus builds.', deleteError: 'Não foi possível excluir o build.', emptyTitle: 'Nenhum build próprio ainda', emptyText: 'Crie seu primeiro build para iniciar sua biblioteca pessoal.', createFirst: 'Criar primeiro build', confirmDelete: 'Excluir este build da sua biblioteca?', delete: 'Excluir', deleteNow: 'Excluir agora', open: 'Abrir meus builds', profileCardTitle: 'Meus builds', profileCardText: 'Uma área compacta para gerenciar builds que você criou, como um mini painel admin para seu conteúdo.' },
    profile: { password: { eyebrow: 'Segurança', title: 'Alterar senha', subtitle: 'Atualize sua senha sem mudar seu perfil.', current: 'Senha atual', new: 'Nova senha', repeat: 'Repetir nova senha', save: 'Atualizar senha', saving: 'Atualizando ...', changed: 'Senha alterada.', repeatMismatch: 'As novas senhas não coincidem.', changeError: 'Não foi possível alterar a senha.' } },
  },
  ru: {
    auth: { loginEyebrow: 'С возвращением', loginTitle: 'Войдите в хаб', loginSubtitle: 'Используйте простую сессию для профиля, своих билдов и доступных staff-инструментов.', usernamePlaceholder: 'Ваш логин', passwordPlaceholder: 'Ваш пароль', sessionHint: 'Этот MVP использует безопасный HttpOnly session cookie, не JWT.', loginBenefitsLabel: 'Преимущества входа',
      loginBenefits: { profile: 'Настройки профиля', myBuilds: 'Ваши билды', staff: 'Staff-инструменты при доступе' } },
    myBuilds: { eyebrow: 'Рабочая зона билдов', title: 'Мои билды', subtitle: 'Управляйте билдами, которые вы создали. Публичные билды остаются в Build Manager.', summaryOne: '1 свой билд', summaryMany: '{count} своих билдов', create: 'Создать билд', filtersLabel: 'Фильтр своих билдов', manageTitle: 'Ваша библиотека билдов', manageText: 'Ищите по названию, кораблю или типу и удаляйте устаревшие личные билды.', searchPlaceholder: 'Искать свои билды по названию, кораблю или типу ...', loading: 'Загрузка ваших билдов ...', loadError: 'Не удалось загрузить ваши билды.', deleteError: 'Не удалось удалить билд.', emptyTitle: 'Своих билдов пока нет', emptyText: 'Создайте первый билд, чтобы начать личную библиотеку.', createFirst: 'Создать первый билд', confirmDelete: 'Удалить этот билд из библиотеки?', delete: 'Удалить', deleteNow: 'Удалить сейчас', open: 'Открыть мои билды', profileCardTitle: 'Мои билды', profileCardText: 'Компактная зона управления созданными вами билдами — мини-панель администратора для своего контента.' },
    profile: { password: { eyebrow: 'Безопасность', title: 'Сменить пароль', subtitle: 'Обновите пароль без изменения профиля.', current: 'Текущий пароль', new: 'Новый пароль', repeat: 'Повторите новый пароль', save: 'Обновить пароль', saving: 'Обновление ...', changed: 'Пароль изменён.', repeatMismatch: 'Новые пароли не совпадают.', changeError: 'Не удалось изменить пароль.' } },
  },
  cn: {
    auth: { loginEyebrow: '欢迎回来', loginTitle: '登录社区中心', loginSubtitle: '使用简单会话登录来管理个人资料、自己的配置和可用的管理工具。', usernamePlaceholder: '用户名', passwordPlaceholder: '密码', sessionHint: '此 MVP 使用安全的 HttpOnly 会话 Cookie，不使用 JWT。', loginBenefitsLabel: '登录权益',
      loginBenefits: { profile: '个人资料设置', myBuilds: '我的配置', staff: '有权限时的管理工具' } },
    myBuilds: { eyebrow: '配置工作区', title: '我的配置', subtitle: '管理你自己创建的配置。公共配置仍会显示在 Build Manager 中。', summaryOne: '1 个自己的配置', summaryMany: '{count} 个自己的配置', create: '创建配置', filtersLabel: '筛选我的配置', manageTitle: '我的配置库', manageText: '按名称、船只或类型搜索，并删除过时的个人配置。', searchPlaceholder: '按名称、船只或类型搜索我的配置 ...', loading: '正在加载我的配置 ...', loadError: '无法加载我的配置。', deleteError: '无法删除配置。', emptyTitle: '还没有自己的配置', emptyText: '创建第一个配置，开始建立个人配置库。', createFirst: '创建第一个配置', confirmDelete: '从你的库中删除此配置？', delete: '删除', deleteNow: '立即删除', open: '打开我的配置', profileCardTitle: '我的配置', profileCardText: '用于管理自己创建配置的紧凑区域，类似个人内容的小型管理面板。' },
    profile: { password: { eyebrow: '安全', title: '修改密码', subtitle: '无需更改个人资料即可更新密码。', current: '当前密码', new: '新密码', repeat: '重复新密码', save: '更新密码', saving: '正在更新 ...', changed: '密码已更改。', repeatMismatch: '两次新密码不一致。', changeError: '无法更改密码。' } },
  },
}


const groupManagementMessages = {
  "en": {
    "common": {
      "groups": "Groups"
    },
    "home": {
      "showcase": {
        "groups": {
          "eyebrow": "New module",
          "title": "Group Management",
          "description": "Find open crews, create simple group calls and join with a ship from the seeded catalog.",
          "metaPublic": "Public list",
          "metaJoin": "Guest join",
          "metaManage": "Own groups"
        }
      }
    },
    "groups": {
      "focus": {
        "all": "All focuses"
      },
      "status": {
        "open": "Open",
        "full": "Full",
        "closed": "Closed"
      },
      "fields": {
        "title": "Title",
        "focus": "Focus",
        "description": "Description",
        "maxMembers": "Max members",
        "minShipRate": "Weakest allowed rate",
        "maxShipRate": "Strongest allowed rate",
        "rateRange": "Allowed rate range",
        "allowGuests": "Allow guests",
        "fleetRestriction": "Fleet restriction",
        "status": "Status",
        "members": "Members",
        "leader": "Leader",
        "guests": "Guests",
        "displayName": "Display name",
        "fleetName": "Fleet",
        "ship": "Ship",
        "note": "Note"
      },
      "list": {
        "title": "Group Management",
        "subtitle": "A minimal board for open WoSB groups. Create a call, join a crew and keep the flow simple.",
        "summaryOne": "1 group found",
        "summaryMany": "{count} groups found",
        "newGroup": "New group",
        "loginToCreate": "Login to create",
        "filtersLabel": "Group filters",
        "filtersTitle": "Find a group",
        "filtersText": "Search by name, focus, fleet note and ship-rate range. Ship-of-the-Line rates count down: 1 is strongest, 7 is lightest.",
        "searchPlaceholder": "Search by group, focus or fleet ...",
        "loading": "Loading groups ...",
        "loadError": "Groups could not be loaded.",
        "empty": "No active groups found.",
        "members": "{current}/{max} members",
        "minRate": "Rate {value} or better",
        "maxRate": "Rate {value} or lighter",
        "rateRange": "Rates {max}–{min}",
        "guestsAllowed": "Guests allowed",
        "leader": "Leader: {name}",
        "spotsLeft": "{count} spots left",
        "noFleetRestriction": "No fleet restriction",
        "noDescription": "No description yet.",
        "anyMaxRate": "Any strongest rate",
        "anyMinRate": "Any weakest rate",
        "rateFilterHint": "Combine strongest and weakest rate to filter by a span, e.g. strongest 2 and weakest 4 shows groups for rates 2–4.",
        "rateFilterInvalid": "The strongest allowed rate must be numerically lower than or equal to the weakest allowed rate."
      },
      "create": {
        "title": "New group",
        "subtitle": "Create a compact group call. Details can stay light for the MVP.",
        "titlePlaceholder": "e.g. Evening farming run",
        "fleetPlaceholder": "Optional fleet note or restriction",
        "descriptionPlaceholder": "Goal, voice chat, ship expectations, route ...",
        "anyRate": "Any rate",
        "anyMaxRate": "Any strongest rate",
        "anyMinRate": "Any weakest rate",
        "allowGuestsHint": "Guests may join without an account.",
        "save": "Create group",
        "saving": "Creating ...",
        "saveError": "Group could not be created.",
        "rateRangeInvalid": "Strongest allowed rate must be numerically lower than or equal to weakest allowed rate.",
        "sections": {
          "basics": "Basics",
          "basicsText": "Name the group and choose the main focus.",
          "requirements": "Requirements",
          "requirementsText": "Set places, guest access and an optional allowed ship-rate span.",
          "details": "Details",
          "detailsText": "Add only what players need before joining."
        }
      },
      "detail": {
        "loading": "Loading group ...",
        "loadError": "Group could not be loaded.",
        "noDescription": "No description saved for this group.",
        "anyRate": "Any",
        "guestsYes": "Allowed",
        "guestsNo": "Login only",
        "membersEyebrow": "Crew",
        "membersTitle": "Current members",
        "spotsLeft": "spots left",
        "noMembers": "No members yet.",
        "noFleet": "No fleet",
        "noShip": "No ship selected",
        "guest": "Guest",
        "member": "Member",
        "joinEyebrow": "Join",
        "joinTitle": "Join this group",
        "joinText": "Choose a display name and optionally a ship. Registered users keep their profile data as default.",
        "joinTextWithRate": "This group accepts ships in the allowed range: {requirement}. Outside rates are disabled.",
        "minRateRequirement": "rate {rate} or better",
        "maxRateRequirement": "rate {rate} or lighter",
        "rateRangeRequirement": "rates {max}–{min}",
        "noShipSelection": "No ship selected",
        "selectRequiredShip": "Select a ship: {requirement}",
        "rateRequired": "Select a ship in the allowed range ({requirement}) before joining.",
        "rateTooLow": "The selected ship is outside the allowed range ({requirement}).",
        "rateOk": "Selected ship is allowed: rate {rate}.",
        "rateLocked": "allowed: {requirement}",
        "join": "Join group",
        "joining": "Joining ...",
        "joined": "You joined the group.",
        "joinError": "Could not join this group.",
        "joinClosedEyebrow": "Closed",
        "joinClosedTitle": "Joining is not available",
        "joinClosedText": "This group is currently full or closed.",
        "close": "Close group",
        "closing": "Closing ...",
        "closeError": "Group could not be closed."
      }
    },
    "myGroups": {
      "eyebrow": "Group workspace",
      "title": "My groups",
      "subtitle": "Manage group calls you created yourself.",
      "summaryOne": "1 own group",
      "summaryMany": "{count} own groups",
      "create": "Create group",
      "manageTitle": "Your group calls",
      "manageText": "Search your own groups and close calls that are no longer active.",
      "searchPlaceholder": "Search your groups ...",
      "loading": "Loading your groups ...",
      "loadError": "Your groups could not be loaded.",
      "closeError": "Group could not be closed.",
      "emptyText": "You have not created a group yet.",
      "confirmClose": "Close this group?",
      "close": "Close",
      "closeNow": "Close now",
      "open": "Open my groups",
      "profileCardTitle": "My groups",
      "profileCardText": "A small management area for group calls you created. Close finished calls and keep your overview tidy."
    }
  },
  "de": {
    "common": {
      "groups": "Gruppen"
    },
    "home": {
      "showcase": {
        "groups": {
          "eyebrow": "Neues Modul",
          "title": "Gruppenverwaltung",
          "description": "Finde offene Crews, erstelle einfache Gruppenaufrufe und tritt mit einem Schiff aus dem Katalog bei.",
          "metaPublic": "Öffentliche Liste",
          "metaJoin": "Gastbeitritt",
          "metaManage": "Eigene Gruppen"
        }
      }
    },
    "groups": {
      "focus": {
        "all": "Alle Fokusse"
      },
      "status": {
        "open": "Offen",
        "full": "Voll",
        "closed": "Geschlossen"
      },
      "fields": {
        "title": "Titel",
        "focus": "Fokus",
        "description": "Beschreibung",
        "maxMembers": "Max. Mitglieder",
        "minShipRate": "Schwächste erlaubte Rate",
        "maxShipRate": "Stärkste erlaubte Rate",
        "rateRange": "Erlaubte Rate-Spanne",
        "allowGuests": "Gäste erlauben",
        "fleetRestriction": "Flottenhinweis",
        "status": "Status",
        "members": "Mitglieder",
        "leader": "Leitung",
        "guests": "Gäste",
        "displayName": "Anzeigename",
        "fleetName": "Flotte",
        "ship": "Schiff",
        "note": "Notiz"
      },
      "list": {
        "title": "Gruppenverwaltung",
        "subtitle": "Ein minimales Board für offene WoSB-Gruppen. Erstelle Aufrufe, finde Crews und halte den Ablauf einfach.",
        "summaryOne": "1 Gruppe gefunden",
        "summaryMany": "{count} Gruppen gefunden",
        "newGroup": "Neue Gruppe",
        "loginToCreate": "Einloggen zum Erstellen",
        "filtersLabel": "Gruppenfilter",
        "filtersTitle": "Gruppe finden",
        "filtersText": "Suche nach Name, Fokus, Flottenhinweis und Schiffsraten-Spanne. Ship-of-the-Line-Raten zählen abwärts: 1 ist am stärksten, 7 am leichtesten.",
        "searchPlaceholder": "Nach Gruppe, Fokus oder Flotte suchen ...",
        "loading": "Gruppen werden geladen ...",
        "loadError": "Gruppen konnten nicht geladen werden.",
        "empty": "Keine aktiven Gruppen gefunden.",
        "members": "{current}/{max} Mitglieder",
        "minRate": "Rate {value} oder besser",
        "maxRate": "Rate {value} oder leichter",
        "rateRange": "Raten {max}–{min}",
        "guestsAllowed": "Gäste erlaubt",
        "leader": "Leitung: {name}",
        "spotsLeft": "{count} Plätze frei",
        "noFleetRestriction": "Keine Flottenbeschränkung",
        "noDescription": "Noch keine Beschreibung.",
        "anyMaxRate": "Keine stärkste Rate",
        "anyMinRate": "Keine schwächste Rate",
        "rateFilterHint": "Kombiniere stärkste und schwächste Rate als Spanne, z. B. stärkste 2 und schwächste 4 für Raten 2–4.",
        "rateFilterInvalid": "Die stärkste erlaubte Rate muss numerisch kleiner oder gleich der schwächsten erlaubten Rate sein."
      },
      "create": {
        "title": "Neue Gruppe",
        "subtitle": "Erstelle einen kompakten Gruppenaufruf. Details können im MVP knapp bleiben.",
        "titlePlaceholder": "z. B. Farmingrunde am Abend",
        "fleetPlaceholder": "Optionaler Flottenhinweis",
        "descriptionPlaceholder": "Ziel, Voice, Schiffserwartung, Route ...",
        "anyRate": "Beliebige Rate",
        "anyMaxRate": "Keine stärkste Rate",
        "anyMinRate": "Keine schwächste Rate",
        "allowGuestsHint": "Gäste dürfen ohne Account beitreten.",
        "save": "Gruppe erstellen",
        "saving": "Erstellt ...",
        "saveError": "Gruppe konnte nicht erstellt werden.",
        "rateRangeInvalid": "Die stärkste erlaubte Rate muss numerisch kleiner oder gleich der schwächsten erlaubten Rate sein.",
        "sections": {
          "basics": "Basis",
          "basicsText": "Benenne die Gruppe und wähle den Fokus.",
          "requirements": "Anforderungen",
          "requirementsText": "Setze Plätze, Gastzugriff und optional eine erlaubte Schiffsraten-Spanne.",
          "details": "Details",
          "detailsText": "Nur hinzufügen, was Spieler vor dem Beitritt brauchen."
        }
      },
      "detail": {
        "loading": "Gruppe wird geladen ...",
        "loadError": "Gruppe konnte nicht geladen werden.",
        "noDescription": "Keine Beschreibung gespeichert.",
        "anyRate": "Beliebig",
        "guestsYes": "Erlaubt",
        "guestsNo": "Nur Login",
        "membersEyebrow": "Crew",
        "membersTitle": "Aktuelle Mitglieder",
        "spotsLeft": "Plätze frei",
        "noMembers": "Noch keine Mitglieder.",
        "noFleet": "Keine Flotte",
        "noShip": "Kein Schiff gewählt",
        "guest": "Gast",
        "member": "Mitglied",
        "joinEyebrow": "Beitreten",
        "joinTitle": "Dieser Gruppe beitreten",
        "joinText": "Wähle einen Anzeigenamen und optional ein Schiff. Eingeloggte Nutzer nutzen ihre Profildaten als Vorgabe.",
        "joinTextWithRate": "Diese Gruppe akzeptiert Schiffe in der erlaubten Spanne: {requirement}. Andere Raten sind deaktiviert.",
        "minRateRequirement": "Rate {rate} oder besser",
        "maxRateRequirement": "Rate {rate} oder leichter",
        "rateRangeRequirement": "Raten {max}–{min}",
        "noShipSelection": "Kein Schiff gewählt",
        "selectRequiredShip": "Schiff wählen: {requirement}",
        "rateRequired": "Wähle vor dem Beitritt ein Schiff in der erlaubten Spanne ({requirement}).",
        "rateTooLow": "Das gewählte Schiff liegt außerhalb der erlaubten Spanne ({requirement}).",
        "rateOk": "Das gewählte Schiff ist erlaubt: Rate {rate}.",
        "rateLocked": "erlaubt: {requirement}",
        "join": "Beitreten",
        "joining": "Tritt bei ...",
        "joined": "Du bist der Gruppe beigetreten.",
        "joinError": "Beitritt nicht möglich.",
        "joinClosedEyebrow": "Geschlossen",
        "joinClosedTitle": "Beitritt nicht verfügbar",
        "joinClosedText": "Diese Gruppe ist voll oder geschlossen.",
        "close": "Gruppe schließen",
        "closing": "Schließt ...",
        "closeError": "Gruppe konnte nicht geschlossen werden."
      }
    },
    "myGroups": {
      "eyebrow": "Gruppenbereich",
      "title": "Meine Gruppen",
      "subtitle": "Verwalte die Gruppenaufrufe, die du erstellt hast.",
      "summaryOne": "1 eigene Gruppe",
      "summaryMany": "{count} eigene Gruppen",
      "create": "Gruppe erstellen",
      "manageTitle": "Deine Gruppenaufrufe",
      "manageText": "Suche eigene Gruppen und schließe erledigte Aufrufe.",
      "searchPlaceholder": "Eigene Gruppen suchen ...",
      "loading": "Eigene Gruppen werden geladen ...",
      "loadError": "Eigene Gruppen konnten nicht geladen werden.",
      "closeError": "Gruppe konnte nicht geschlossen werden.",
      "emptyText": "Du hast noch keine Gruppe erstellt.",
      "confirmClose": "Diese Gruppe schließen?",
      "close": "Schließen",
      "closeNow": "Jetzt schließen",
      "open": "Meine Gruppen öffnen",
      "profileCardTitle": "Meine Gruppen",
      "profileCardText": "Ein kleiner Verwaltungsbereich für von dir erstellte Gruppenaufrufe."
    }
  },
  "fr": {
    "common": {
      "groups": "Groupes"
    },
    "home": {
      "showcase": {
        "groups": {
          "eyebrow": "New module",
          "title": "Gestion des groupes",
          "description": "Find open crews, create simple group calls and join with a ship from the seeded catalog.",
          "metaPublic": "Public list",
          "metaJoin": "Guest join",
          "metaManage": "Own groups"
        }
      }
    },
    "groups": {
      "focus": {
        "all": "Tous les focus"
      },
      "status": {
        "open": "Ouvert",
        "full": "Complet",
        "closed": "Fermé"
      },
      "fields": {
        "title": "Title",
        "focus": "Focus",
        "description": "Description",
        "maxMembers": "Max members",
        "minShipRate": "Weakest allowed Rang",
        "maxShipRate": "Strongest allowed Rang",
        "rateRange": "Allowed Rang range",
        "allowGuests": "Allow guests",
        "fleetRestriction": "Fleet restriction",
        "status": "Status",
        "members": "Members",
        "leader": "Leader",
        "guests": "Guests",
        "displayName": "Display name",
        "fleetName": "Fleet",
        "ship": "Ship",
        "note": "Note"
      },
      "list": {
        "title": "Gestion des groupes",
        "subtitle": "A minimal board for open WoSB groups. Create a call, join a crew and keep the flow simple.",
        "summaryOne": "1 group found",
        "summaryMany": "{count} groups found",
        "newGroup": "Nouveau groupe",
        "loginToCreate": "Login to create",
        "filtersLabel": "Group filters",
        "filtersTitle": "Find a group",
        "filtersText": "Search by name, focus, fleet note and ship-rate range. Ship-of-the-Line rates count down: 1 is strongest, 7 is lightest.",
        "searchPlaceholder": "Search by group, focus or fleet ...",
        "loading": "Loading groups ...",
        "loadError": "Groups could not be loaded.",
        "empty": "No active groups found.",
        "members": "{current}/{max} members",
        "minRate": "Rate {value} or better",
        "maxRate": "Rate {value} or lighter",
        "rateRange": "Rates {max}–{min}",
        "guestsAllowed": "Guests allowed",
        "leader": "Leader: {name}",
        "spotsLeft": "{count} spots left",
        "noFleetRestriction": "No fleet restriction",
        "noDescription": "No description yet.",
        "anyMaxRate": "Any strongest Rang",
        "anyMinRate": "Any weakest Rang",
        "rateFilterHint": "Combine strongest and weakest rate to filter by a span, e.g. strongest 2 and weakest 4 shows groups for rates 2–4.",
        "rateFilterInvalid": "The strongest allowed rate must be numerically lower than or equal to the weakest allowed rate."
      },
      "create": {
        "title": "Nouveau groupe",
        "subtitle": "Create a compact group call. Details can stay light for the MVP.",
        "titlePlaceholder": "e.g. Evening farming run",
        "fleetPlaceholder": "Optional fleet note or restriction",
        "descriptionPlaceholder": "Goal, voice chat, ship expectations, route ...",
        "anyRate": "Any Rang",
        "anyMaxRate": "Any strongest Rang",
        "anyMinRate": "Any weakest Rang",
        "allowGuestsHint": "Guests may join without an account.",
        "save": "Créer un groupe",
        "saving": "Creating ...",
        "saveError": "Group could not be created.",
        "rateRangeInvalid": "Strongest allowed rate must be numerically lower than or equal to weakest allowed rate.",
        "sections": {
          "basics": "Basics",
          "basicsText": "Name the group and choose the main focus.",
          "requirements": "Requirements",
          "requirementsText": "Set places, guest access and an optional allowed ship-rate span.",
          "details": "Details",
          "detailsText": "Add only what players need before joining."
        }
      },
      "detail": {
        "loading": "Loading group ...",
        "loadError": "Group could not be loaded.",
        "noDescription": "No description saved for this group.",
        "anyRate": "Any",
        "guestsYes": "Allowed",
        "guestsNo": "Login only",
        "membersEyebrow": "Crew",
        "membersTitle": "Current members",
        "spotsLeft": "spots left",
        "noMembers": "No members yet.",
        "noFleet": "No fleet",
        "noShip": "No ship selected",
        "guest": "Guest",
        "member": "Member",
        "joinEyebrow": "Join",
        "joinTitle": "Join this group",
        "joinText": "Choose a display name and optionally a ship. Registered users keep their profile data as default.",
        "joinTextWithRate": "This group accepts ships in the allowed range: {requirement}. Outside rates are disabled.",
        "minRateRequirement": "rate {rate} or better",
        "maxRateRequirement": "rate {rate} or lighter",
        "rateRangeRequirement": "rates {max}–{min}",
        "noShipSelection": "No ship selected",
        "selectRequiredShip": "Select a ship: {requirement}",
        "rateRequired": "Select a ship in the allowed range ({requirement}) before joining.",
        "rateTooLow": "The selected ship is outside the allowed range ({requirement}).",
        "rateOk": "Selected ship is allowed: rate {rate}.",
        "rateLocked": "allowed: {requirement}",
        "join": "Join group",
        "joining": "Joining ...",
        "joined": "You joined the group.",
        "joinError": "Could not join this group.",
        "joinClosedEyebrow": "Closed",
        "joinClosedTitle": "Joining is not available",
        "joinClosedText": "This group is currently full or closed.",
        "close": "Close group",
        "closing": "Closing ...",
        "closeError": "Group could not be closed."
      }
    },
    "myGroups": {
      "eyebrow": "Group workspace",
      "title": "Mes groupes",
      "subtitle": "Manage group calls you created yourself.",
      "summaryOne": "1 own group",
      "summaryMany": "{count} own groups",
      "create": "Créer un groupe",
      "manageTitle": "Your group calls",
      "manageText": "Search your own groups and close calls that are no longer active.",
      "searchPlaceholder": "Search your groups ...",
      "loading": "Loading your groups ...",
      "loadError": "Your groups could not be loaded.",
      "closeError": "Group could not be closed.",
      "emptyText": "You have not created a group yet.",
      "confirmClose": "Close this group?",
      "close": "Close",
      "closeNow": "Close now",
      "open": "Open my groups",
      "profileCardTitle": "My groups",
      "profileCardText": "A small management area for group calls you created. Close finished calls and keep your overview tidy."
    }
  },
  "es": {
    "common": {
      "groups": "Grupos"
    },
    "home": {
      "showcase": {
        "groups": {
          "eyebrow": "New module",
          "title": "Gestión de grupos",
          "description": "Find open crews, create simple group calls and join with a ship from the seeded catalog.",
          "metaPublic": "Public list",
          "metaJoin": "Guest join",
          "metaManage": "Own groups"
        }
      }
    },
    "groups": {
      "focus": {
        "all": "Todos los enfoques"
      },
      "status": {
        "open": "Abierto",
        "full": "Completo",
        "closed": "Cerrado"
      },
      "fields": {
        "title": "Title",
        "focus": "Focus",
        "description": "Description",
        "maxMembers": "Max members",
        "minShipRate": "Weakest allowed Clase",
        "maxShipRate": "Strongest allowed Clase",
        "rateRange": "Allowed Clase range",
        "allowGuests": "Allow guests",
        "fleetRestriction": "Fleet restriction",
        "status": "Status",
        "members": "Members",
        "leader": "Leader",
        "guests": "Guests",
        "displayName": "Display name",
        "fleetName": "Fleet",
        "ship": "Ship",
        "note": "Note"
      },
      "list": {
        "title": "Gestión de grupos",
        "subtitle": "A minimal board for open WoSB groups. Create a call, join a crew and keep the flow simple.",
        "summaryOne": "1 group found",
        "summaryMany": "{count} groups found",
        "newGroup": "Nuevo grupo",
        "loginToCreate": "Login to create",
        "filtersLabel": "Group filters",
        "filtersTitle": "Find a group",
        "filtersText": "Search by name, focus, fleet note and ship-rate range. Ship-of-the-Line rates count down: 1 is strongest, 7 is lightest.",
        "searchPlaceholder": "Search by group, focus or fleet ...",
        "loading": "Loading groups ...",
        "loadError": "Groups could not be loaded.",
        "empty": "No active groups found.",
        "members": "{current}/{max} members",
        "minRate": "Rate {value} or better",
        "maxRate": "Rate {value} or lighter",
        "rateRange": "Rates {max}–{min}",
        "guestsAllowed": "Guests allowed",
        "leader": "Leader: {name}",
        "spotsLeft": "{count} spots left",
        "noFleetRestriction": "No fleet restriction",
        "noDescription": "No description yet.",
        "anyMaxRate": "Any strongest Clase",
        "anyMinRate": "Any weakest Clase",
        "rateFilterHint": "Combine strongest and weakest rate to filter by a span, e.g. strongest 2 and weakest 4 shows groups for rates 2–4.",
        "rateFilterInvalid": "The strongest allowed rate must be numerically lower than or equal to the weakest allowed rate."
      },
      "create": {
        "title": "Nuevo grupo",
        "subtitle": "Create a compact group call. Details can stay light for the MVP.",
        "titlePlaceholder": "e.g. Evening farming run",
        "fleetPlaceholder": "Optional fleet note or restriction",
        "descriptionPlaceholder": "Goal, voice chat, ship expectations, route ...",
        "anyRate": "Any Clase",
        "anyMaxRate": "Any strongest Clase",
        "anyMinRate": "Any weakest Clase",
        "allowGuestsHint": "Guests may join without an account.",
        "save": "Crear grupo",
        "saving": "Creating ...",
        "saveError": "Group could not be created.",
        "rateRangeInvalid": "Strongest allowed rate must be numerically lower than or equal to weakest allowed rate.",
        "sections": {
          "basics": "Basics",
          "basicsText": "Name the group and choose the main focus.",
          "requirements": "Requirements",
          "requirementsText": "Set places, guest access and an optional allowed ship-rate span.",
          "details": "Details",
          "detailsText": "Add only what players need before joining."
        }
      },
      "detail": {
        "loading": "Loading group ...",
        "loadError": "Group could not be loaded.",
        "noDescription": "No description saved for this group.",
        "anyRate": "Any",
        "guestsYes": "Allowed",
        "guestsNo": "Login only",
        "membersEyebrow": "Crew",
        "membersTitle": "Current members",
        "spotsLeft": "spots left",
        "noMembers": "No members yet.",
        "noFleet": "No fleet",
        "noShip": "No ship selected",
        "guest": "Guest",
        "member": "Member",
        "joinEyebrow": "Join",
        "joinTitle": "Join this group",
        "joinText": "Choose a display name and optionally a ship. Registered users keep their profile data as default.",
        "joinTextWithRate": "This group accepts ships in the allowed range: {requirement}. Outside rates are disabled.",
        "minRateRequirement": "rate {rate} or better",
        "maxRateRequirement": "rate {rate} or lighter",
        "rateRangeRequirement": "rates {max}–{min}",
        "noShipSelection": "No ship selected",
        "selectRequiredShip": "Select a ship: {requirement}",
        "rateRequired": "Select a ship in the allowed range ({requirement}) before joining.",
        "rateTooLow": "The selected ship is outside the allowed range ({requirement}).",
        "rateOk": "Selected ship is allowed: rate {rate}.",
        "rateLocked": "allowed: {requirement}",
        "join": "Join group",
        "joining": "Joining ...",
        "joined": "You joined the group.",
        "joinError": "Could not join this group.",
        "joinClosedEyebrow": "Closed",
        "joinClosedTitle": "Joining is not available",
        "joinClosedText": "This group is currently full or closed.",
        "close": "Close group",
        "closing": "Closing ...",
        "closeError": "Group could not be closed."
      }
    },
    "myGroups": {
      "eyebrow": "Group workspace",
      "title": "Mis grupos",
      "subtitle": "Manage group calls you created yourself.",
      "summaryOne": "1 own group",
      "summaryMany": "{count} own groups",
      "create": "Crear grupo",
      "manageTitle": "Your group calls",
      "manageText": "Search your own groups and close calls that are no longer active.",
      "searchPlaceholder": "Search your groups ...",
      "loading": "Loading your groups ...",
      "loadError": "Your groups could not be loaded.",
      "closeError": "Group could not be closed.",
      "emptyText": "You have not created a group yet.",
      "confirmClose": "Close this group?",
      "close": "Close",
      "closeNow": "Close now",
      "open": "Open my groups",
      "profileCardTitle": "My groups",
      "profileCardText": "A small management area for group calls you created. Close finished calls and keep your overview tidy."
    }
  },
  "pt": {
    "common": {
      "groups": "Grupos"
    },
    "home": {
      "showcase": {
        "groups": {
          "eyebrow": "New module",
          "title": "Gerenciamento de grupos",
          "description": "Find open crews, create simple group calls and join with a ship from the seeded catalog.",
          "metaPublic": "Public list",
          "metaJoin": "Guest join",
          "metaManage": "Own groups"
        }
      }
    },
    "groups": {
      "focus": {
        "all": "Todos os focos"
      },
      "status": {
        "open": "Aberto",
        "full": "Cheio",
        "closed": "Fechado"
      },
      "fields": {
        "title": "Title",
        "focus": "Focus",
        "description": "Description",
        "maxMembers": "Max members",
        "minShipRate": "Weakest allowed Classe",
        "maxShipRate": "Strongest allowed Classe",
        "rateRange": "Allowed Classe range",
        "allowGuests": "Allow guests",
        "fleetRestriction": "Fleet restriction",
        "status": "Status",
        "members": "Members",
        "leader": "Leader",
        "guests": "Guests",
        "displayName": "Display name",
        "fleetName": "Fleet",
        "ship": "Ship",
        "note": "Note"
      },
      "list": {
        "title": "Gerenciamento de grupos",
        "subtitle": "A minimal board for open WoSB groups. Create a call, join a crew and keep the flow simple.",
        "summaryOne": "1 group found",
        "summaryMany": "{count} groups found",
        "newGroup": "Novo grupo",
        "loginToCreate": "Login to create",
        "filtersLabel": "Group filters",
        "filtersTitle": "Find a group",
        "filtersText": "Search by name, focus, fleet note and ship-rate range. Ship-of-the-Line rates count down: 1 is strongest, 7 is lightest.",
        "searchPlaceholder": "Search by group, focus or fleet ...",
        "loading": "Loading groups ...",
        "loadError": "Groups could not be loaded.",
        "empty": "No active groups found.",
        "members": "{current}/{max} members",
        "minRate": "Rate {value} or better",
        "maxRate": "Rate {value} or lighter",
        "rateRange": "Rates {max}–{min}",
        "guestsAllowed": "Guests allowed",
        "leader": "Leader: {name}",
        "spotsLeft": "{count} spots left",
        "noFleetRestriction": "No fleet restriction",
        "noDescription": "No description yet.",
        "anyMaxRate": "Any strongest Classe",
        "anyMinRate": "Any weakest Classe",
        "rateFilterHint": "Combine strongest and weakest rate to filter by a span, e.g. strongest 2 and weakest 4 shows groups for rates 2–4.",
        "rateFilterInvalid": "The strongest allowed rate must be numerically lower than or equal to the weakest allowed rate."
      },
      "create": {
        "title": "Novo grupo",
        "subtitle": "Create a compact group call. Details can stay light for the MVP.",
        "titlePlaceholder": "e.g. Evening farming run",
        "fleetPlaceholder": "Optional fleet note or restriction",
        "descriptionPlaceholder": "Goal, voice chat, ship expectations, route ...",
        "anyRate": "Any Classe",
        "anyMaxRate": "Any strongest Classe",
        "anyMinRate": "Any weakest Classe",
        "allowGuestsHint": "Guests may join without an account.",
        "save": "Criar grupo",
        "saving": "Creating ...",
        "saveError": "Group could not be created.",
        "rateRangeInvalid": "Strongest allowed rate must be numerically lower than or equal to weakest allowed rate.",
        "sections": {
          "basics": "Basics",
          "basicsText": "Name the group and choose the main focus.",
          "requirements": "Requirements",
          "requirementsText": "Set places, guest access and an optional allowed ship-rate span.",
          "details": "Details",
          "detailsText": "Add only what players need before joining."
        }
      },
      "detail": {
        "loading": "Loading group ...",
        "loadError": "Group could not be loaded.",
        "noDescription": "No description saved for this group.",
        "anyRate": "Any",
        "guestsYes": "Allowed",
        "guestsNo": "Login only",
        "membersEyebrow": "Crew",
        "membersTitle": "Current members",
        "spotsLeft": "spots left",
        "noMembers": "No members yet.",
        "noFleet": "No fleet",
        "noShip": "No ship selected",
        "guest": "Guest",
        "member": "Member",
        "joinEyebrow": "Join",
        "joinTitle": "Join this group",
        "joinText": "Choose a display name and optionally a ship. Registered users keep their profile data as default.",
        "joinTextWithRate": "This group accepts ships in the allowed range: {requirement}. Outside rates are disabled.",
        "minRateRequirement": "rate {rate} or better",
        "maxRateRequirement": "rate {rate} or lighter",
        "rateRangeRequirement": "rates {max}–{min}",
        "noShipSelection": "No ship selected",
        "selectRequiredShip": "Select a ship: {requirement}",
        "rateRequired": "Select a ship in the allowed range ({requirement}) before joining.",
        "rateTooLow": "The selected ship is outside the allowed range ({requirement}).",
        "rateOk": "Selected ship is allowed: rate {rate}.",
        "rateLocked": "allowed: {requirement}",
        "join": "Join group",
        "joining": "Joining ...",
        "joined": "You joined the group.",
        "joinError": "Could not join this group.",
        "joinClosedEyebrow": "Closed",
        "joinClosedTitle": "Joining is not available",
        "joinClosedText": "This group is currently full or closed.",
        "close": "Close group",
        "closing": "Closing ...",
        "closeError": "Group could not be closed."
      }
    },
    "myGroups": {
      "eyebrow": "Group workspace",
      "title": "Meus grupos",
      "subtitle": "Manage group calls you created yourself.",
      "summaryOne": "1 own group",
      "summaryMany": "{count} own groups",
      "create": "Criar grupo",
      "manageTitle": "Your group calls",
      "manageText": "Search your own groups and close calls that are no longer active.",
      "searchPlaceholder": "Search your groups ...",
      "loading": "Loading your groups ...",
      "loadError": "Your groups could not be loaded.",
      "closeError": "Group could not be closed.",
      "emptyText": "You have not created a group yet.",
      "confirmClose": "Close this group?",
      "close": "Close",
      "closeNow": "Close now",
      "open": "Open my groups",
      "profileCardTitle": "My groups",
      "profileCardText": "A small management area for group calls you created. Close finished calls and keep your overview tidy."
    }
  },
  "ru": {
    "common": {
      "groups": "Группы"
    },
    "home": {
      "showcase": {
        "groups": {
          "eyebrow": "New module",
          "title": "Управление группами",
          "description": "Find open crews, create simple group calls and join with a ship from the seeded catalog.",
          "metaPublic": "Public list",
          "metaJoin": "Guest join",
          "metaManage": "Own groups"
        }
      }
    },
    "groups": {
      "focus": {
        "all": "Все фокусы"
      },
      "status": {
        "open": "Открыто",
        "full": "Полная",
        "closed": "Закрыта"
      },
      "fields": {
        "title": "Title",
        "focus": "Focus",
        "description": "Description",
        "maxMembers": "Max members",
        "minShipRate": "Weakest allowed Ранг",
        "maxShipRate": "Strongest allowed Ранг",
        "rateRange": "Allowed Ранг range",
        "allowGuests": "Allow guests",
        "fleetRestriction": "Fleet restriction",
        "status": "Status",
        "members": "Members",
        "leader": "Leader",
        "guests": "Guests",
        "displayName": "Display name",
        "fleetName": "Fleet",
        "ship": "Ship",
        "note": "Note"
      },
      "list": {
        "title": "Управление группами",
        "subtitle": "A minimal board for open WoSB groups. Create a call, join a crew and keep the flow simple.",
        "summaryOne": "1 group found",
        "summaryMany": "{count} groups found",
        "newGroup": "Новая группа",
        "loginToCreate": "Login to create",
        "filtersLabel": "Group filters",
        "filtersTitle": "Find a group",
        "filtersText": "Search by name, focus, fleet note and ship-rate range. Ship-of-the-Line rates count down: 1 is strongest, 7 is lightest.",
        "searchPlaceholder": "Search by group, focus or fleet ...",
        "loading": "Loading groups ...",
        "loadError": "Groups could not be loaded.",
        "empty": "No active groups found.",
        "members": "{current}/{max} members",
        "minRate": "Rate {value} or better",
        "maxRate": "Rate {value} or lighter",
        "rateRange": "Rates {max}–{min}",
        "guestsAllowed": "Guests allowed",
        "leader": "Leader: {name}",
        "spotsLeft": "{count} spots left",
        "noFleetRestriction": "No fleet restriction",
        "noDescription": "No description yet.",
        "anyMaxRate": "Any strongest Ранг",
        "anyMinRate": "Any weakest Ранг",
        "rateFilterHint": "Combine strongest and weakest rate to filter by a span, e.g. strongest 2 and weakest 4 shows groups for rates 2–4.",
        "rateFilterInvalid": "The strongest allowed rate must be numerically lower than or equal to the weakest allowed rate."
      },
      "create": {
        "title": "Новая группа",
        "subtitle": "Create a compact group call. Details can stay light for the MVP.",
        "titlePlaceholder": "e.g. Evening farming run",
        "fleetPlaceholder": "Optional fleet note or restriction",
        "descriptionPlaceholder": "Goal, voice chat, ship expectations, route ...",
        "anyRate": "Any Ранг",
        "anyMaxRate": "Any strongest Ранг",
        "anyMinRate": "Any weakest Ранг",
        "allowGuestsHint": "Guests may join without an account.",
        "save": "Создать группу",
        "saving": "Creating ...",
        "saveError": "Group could not be created.",
        "rateRangeInvalid": "Strongest allowed rate must be numerically lower than or equal to weakest allowed rate.",
        "sections": {
          "basics": "Basics",
          "basicsText": "Name the group and choose the main focus.",
          "requirements": "Requirements",
          "requirementsText": "Set places, guest access and an optional allowed ship-rate span.",
          "details": "Details",
          "detailsText": "Add only what players need before joining."
        }
      },
      "detail": {
        "loading": "Loading group ...",
        "loadError": "Group could not be loaded.",
        "noDescription": "No description saved for this group.",
        "anyRate": "Any",
        "guestsYes": "Allowed",
        "guestsNo": "Login only",
        "membersEyebrow": "Crew",
        "membersTitle": "Current members",
        "spotsLeft": "spots left",
        "noMembers": "No members yet.",
        "noFleet": "No fleet",
        "noShip": "No ship selected",
        "guest": "Guest",
        "member": "Member",
        "joinEyebrow": "Join",
        "joinTitle": "Join this group",
        "joinText": "Choose a display name and optionally a ship. Registered users keep their profile data as default.",
        "joinTextWithRate": "This group accepts ships in the allowed range: {requirement}. Outside rates are disabled.",
        "minRateRequirement": "rate {rate} or better",
        "maxRateRequirement": "rate {rate} or lighter",
        "rateRangeRequirement": "rates {max}–{min}",
        "noShipSelection": "No ship selected",
        "selectRequiredShip": "Select a ship: {requirement}",
        "rateRequired": "Select a ship in the allowed range ({requirement}) before joining.",
        "rateTooLow": "The selected ship is outside the allowed range ({requirement}).",
        "rateOk": "Selected ship is allowed: rate {rate}.",
        "rateLocked": "allowed: {requirement}",
        "join": "Join group",
        "joining": "Joining ...",
        "joined": "You joined the group.",
        "joinError": "Could not join this group.",
        "joinClosedEyebrow": "Closed",
        "joinClosedTitle": "Joining is not available",
        "joinClosedText": "This group is currently full or closed.",
        "close": "Close group",
        "closing": "Closing ...",
        "closeError": "Group could not be closed."
      }
    },
    "myGroups": {
      "eyebrow": "Group workspace",
      "title": "Мои группы",
      "subtitle": "Manage group calls you created yourself.",
      "summaryOne": "1 own group",
      "summaryMany": "{count} own groups",
      "create": "Создать группу",
      "manageTitle": "Your group calls",
      "manageText": "Search your own groups and close calls that are no longer active.",
      "searchPlaceholder": "Search your groups ...",
      "loading": "Loading your groups ...",
      "loadError": "Your groups could not be loaded.",
      "closeError": "Group could not be closed.",
      "emptyText": "You have not created a group yet.",
      "confirmClose": "Close this group?",
      "close": "Close",
      "closeNow": "Close now",
      "open": "Open my groups",
      "profileCardTitle": "My groups",
      "profileCardText": "A small management area for group calls you created. Close finished calls and keep your overview tidy."
    }
  },
  "cn": {
    "common": {
      "groups": "小队"
    },
    "home": {
      "showcase": {
        "groups": {
          "eyebrow": "New module",
          "title": "小队管理",
          "description": "Find open crews, create simple group calls and join with a ship from the seeded catalog.",
          "metaPublic": "Public list",
          "metaJoin": "Guest join",
          "metaManage": "Own groups"
        }
      }
    },
    "groups": {
      "focus": {
        "all": "所有重点"
      },
      "status": {
        "open": "开放",
        "full": "已满",
        "closed": "已关闭"
      },
      "fields": {
        "title": "Title",
        "focus": "Focus",
        "description": "Description",
        "maxMembers": "Max members",
        "minShipRate": "Weakest allowed 等级",
        "maxShipRate": "Strongest allowed 等级",
        "rateRange": "Allowed 等级 range",
        "allowGuests": "Allow guests",
        "fleetRestriction": "Fleet restriction",
        "status": "Status",
        "members": "Members",
        "leader": "Leader",
        "guests": "Guests",
        "displayName": "Display name",
        "fleetName": "Fleet",
        "ship": "Ship",
        "note": "Note"
      },
      "list": {
        "title": "小队管理",
        "subtitle": "A minimal board for open WoSB groups. Create a call, join a crew and keep the flow simple.",
        "summaryOne": "1 group found",
        "summaryMany": "{count} groups found",
        "newGroup": "新建小队",
        "loginToCreate": "Login to create",
        "filtersLabel": "Group filters",
        "filtersTitle": "Find a group",
        "filtersText": "Search by name, focus, fleet note and ship-rate range. Ship-of-the-Line rates count down: 1 is strongest, 7 is lightest.",
        "searchPlaceholder": "Search by group, focus or fleet ...",
        "loading": "Loading groups ...",
        "loadError": "Groups could not be loaded.",
        "empty": "No active groups found.",
        "members": "{current}/{max} members",
        "minRate": "Rate {value} or better",
        "maxRate": "Rate {value} or lighter",
        "rateRange": "Rates {max}–{min}",
        "guestsAllowed": "Guests allowed",
        "leader": "Leader: {name}",
        "spotsLeft": "{count} spots left",
        "noFleetRestriction": "No fleet restriction",
        "noDescription": "No description yet.",
        "anyMaxRate": "Any strongest 等级",
        "anyMinRate": "Any weakest 等级",
        "rateFilterHint": "Combine strongest and weakest rate to filter by a span, e.g. strongest 2 and weakest 4 shows groups for rates 2–4.",
        "rateFilterInvalid": "The strongest allowed rate must be numerically lower than or equal to the weakest allowed rate."
      },
      "create": {
        "title": "新建小队",
        "subtitle": "Create a compact group call. Details can stay light for the MVP.",
        "titlePlaceholder": "e.g. Evening farming run",
        "fleetPlaceholder": "Optional fleet note or restriction",
        "descriptionPlaceholder": "Goal, voice chat, ship expectations, route ...",
        "anyRate": "Any 等级",
        "anyMaxRate": "Any strongest 等级",
        "anyMinRate": "Any weakest 等级",
        "allowGuestsHint": "Guests may join without an account.",
        "save": "创建小队",
        "saving": "Creating ...",
        "saveError": "Group could not be created.",
        "rateRangeInvalid": "Strongest allowed rate must be numerically lower than or equal to weakest allowed rate.",
        "sections": {
          "basics": "Basics",
          "basicsText": "Name the group and choose the main focus.",
          "requirements": "Requirements",
          "requirementsText": "Set places, guest access and an optional allowed ship-rate span.",
          "details": "Details",
          "detailsText": "Add only what players need before joining."
        }
      },
      "detail": {
        "loading": "Loading group ...",
        "loadError": "Group could not be loaded.",
        "noDescription": "No description saved for this group.",
        "anyRate": "Any",
        "guestsYes": "Allowed",
        "guestsNo": "Login only",
        "membersEyebrow": "Crew",
        "membersTitle": "Current members",
        "spotsLeft": "spots left",
        "noMembers": "No members yet.",
        "noFleet": "No fleet",
        "noShip": "No ship selected",
        "guest": "Guest",
        "member": "Member",
        "joinEyebrow": "Join",
        "joinTitle": "Join this group",
        "joinText": "Choose a display name and optionally a ship. Registered users keep their profile data as default.",
        "joinTextWithRate": "This group accepts ships in the allowed range: {requirement}. Outside rates are disabled.",
        "minRateRequirement": "rate {rate} or better",
        "maxRateRequirement": "rate {rate} or lighter",
        "rateRangeRequirement": "rates {max}–{min}",
        "noShipSelection": "No ship selected",
        "selectRequiredShip": "Select a ship: {requirement}",
        "rateRequired": "Select a ship in the allowed range ({requirement}) before joining.",
        "rateTooLow": "The selected ship is outside the allowed range ({requirement}).",
        "rateOk": "Selected ship is allowed: rate {rate}.",
        "rateLocked": "allowed: {requirement}",
        "join": "Join group",
        "joining": "Joining ...",
        "joined": "You joined the group.",
        "joinError": "Could not join this group.",
        "joinClosedEyebrow": "Closed",
        "joinClosedTitle": "Joining is not available",
        "joinClosedText": "This group is currently full or closed.",
        "close": "Close group",
        "closing": "Closing ...",
        "closeError": "Group could not be closed."
      }
    },
    "myGroups": {
      "eyebrow": "Group workspace",
      "title": "我的小队",
      "subtitle": "Manage group calls you created yourself.",
      "summaryOne": "1 own group",
      "summaryMany": "{count} own groups",
      "create": "创建小队",
      "manageTitle": "Your group calls",
      "manageText": "Search your own groups and close calls that are no longer active.",
      "searchPlaceholder": "Search your groups ...",
      "loading": "Loading your groups ...",
      "loadError": "Your groups could not be loaded.",
      "closeError": "Group could not be closed.",
      "emptyText": "You have not created a group yet.",
      "confirmClose": "Close this group?",
      "close": "Close",
      "closeNow": "Close now",
      "open": "Open my groups",
      "profileCardTitle": "My groups",
      "profileCardText": "A small management area for group calls you created. Close finished calls and keep your overview tidy."
    }
  }
}

function mergeMessages(target, source) {
  for (const [key, value] of Object.entries(source || {})) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      target[key] = mergeMessages(target[key] || {}, value)
    } else {
      target[key] = value
    }
  }
  return target
}

for (const localeCode of Object.keys(messages)) {
  mergeMessages(messages[localeCode], authAdminProfileMessages.en)
  mergeMessages(messages[localeCode], authAdminProfileMessages[localeCode] || {})
  mergeMessages(messages[localeCode], userBuildsAndPasswordMessages.en)
  mergeMessages(messages[localeCode], userBuildsAndPasswordMessages[localeCode] || {})
  mergeMessages(messages[localeCode], groupManagementMessages.en)
  mergeMessages(messages[localeCode], groupManagementMessages[localeCode] || {})
}

function getNestedValue(source, path) {
  return path.split('.').reduce((current, key) => current?.[key], source)
}

function formatMessage(template, params = {}) {
  return String(template).replace(/\{(\w+)\}/g, (_, key) => String(params[key] ?? `{${key}}`))
}

function normalizeLocale(locale) {
  return SUPPORTED_LOCALES.some((entry) => entry.code === locale) ? locale : DEFAULT_LOCALE
}

function getHtmlLang(locale) {
  return SUPPORTED_LOCALES.find((entry) => entry.code === locale)?.htmlLang || 'en'
}

const initialLocale = normalizeLocale(localStorage.getItem('wosb.locale') || DEFAULT_LOCALE)
const state = reactive({ locale: initialLocale })

document.documentElement.lang = getHtmlLang(initialLocale)

export function setLocale(locale) {
  const normalized = normalizeLocale(locale)
  state.locale = normalized
  localStorage.setItem('wosb.locale', normalized)
  document.documentElement.lang = getHtmlLang(normalized)
}

export function translate(path, params = {}) {
  const localized = getNestedValue(messages[state.locale], path)
  const fallback = getNestedValue(messages[DEFAULT_LOCALE], path)
  return formatMessage(localized ?? fallback ?? path, params)
}

function replaceTerms(value, terms) {
  let output = String(value)
  const orderedTerms = Object.entries(terms || {}).sort((left, right) => right[0].length - left[0].length)

  for (const [source, target] of orderedTerms) {
    output = output.replaceAll(source, target)
  }

  return output
}

export function translateOptionName(name) {
  const value = String(name || '')
  if (!value || state.locale === DEFAULT_LOCALE) return value
  return replaceTerms(value, optionTermGlossaries[state.locale])
}

export function useLocale() {
  return {
    locale: computed(() => state.locale),
    localeState: readonly(state),
    supportedLocales: SUPPORTED_LOCALES,
    setLocale,
    t: translate,
    optionLabel: translateOptionName,
  }
}
