const TEXT_PLACEHOLDER = '__WOSB_PLACEHOLDER_'

const neutralValues = new Set([
  'Iron Crown Fleet Hub', 'Iron Crown Fleet Hub MVP', 'WoSB', 'MVP', 'API', 'PDF', 'GIF', 'MP4', 'JPEG', 'PNG', 'WebP', 'WebM', 'MOV',
  'Forum', 'Guides', 'Admin', 'PvE', 'PvP', 'Support', 'Builds', 'Hold', 'Lanterns', 'Sails', 'Sources', 'Fleet', 'Profiles', 'Weapons',
])

const localePrefixes = {
  de: 'DE',
  fr: 'FR',
  es: 'ES',
  pt: 'PT',
  ru: 'RU',
  cn: 'CN',
}

const exactTranslations = {
  de: {
    'Primary': 'Primär',
    'Account': 'Account',
    'Staff quick actions': 'Team-Schnellaktionen',
  },
  fr: {
    'Primary': 'Principal',
    'Account': 'Compte',
    'Staff quick actions': 'Actions rapides du staff',
    'All categories': 'Toutes les catégories',
    'All types': 'Tous les types',
    'All fleets': 'Toutes les flottes',
    'All statuses': 'Tous les statuts',
    'All roles': 'Tous les rôles',
    'No slots': 'Aucun emplacement',
    'No summary saved.': 'Aucun résumé enregistré.',
    'No details saved.': 'Aucun détail enregistré.',
    'No matching forum threads.': 'Aucun fil de forum correspondant.',
    'No matching guides.': 'Aucun guide correspondant.',
    'No matching fleet announcements.': 'Aucune annonce de flotte correspondante.',
    'No upcoming appointments found.': 'Aucun rendez-vous à venir trouvé.',
    'No builds found.': 'Aucun build trouvé.',
    'No builds yet.': 'Aucun build pour le moment.',
    'No guides yet.': 'Aucun guide pour le moment.',
    'No threads yet.': 'Aucun fil pour le moment.',
    'No account yet?': 'Pas encore de compte ?',
    'Already have an account?': 'Vous avez déjà un compte ?',
    'Create account': 'Créer un compte',
    'Sign in': 'Se connecter',
    'Login failed.': 'Connexion échouée.',
    'Registration failed.': 'Inscription échouée.',
    'Loading ...': 'Chargement ...',
    'Saving ...': 'Enregistrement ...',
    'Creating account ...': 'Création du compte ...',
    'Loading profile ...': 'Chargement du profil ...',
    'Profile saved.': 'Profil enregistré.',
    'Account created. You can sign in now.': 'Compte créé. Vous pouvez vous connecter maintenant.',
    'Delete this build?': 'Supprimer ce build ?',
    'Delete this guide?': 'Supprimer ce guide ?',
    'Cancel this appointment?': 'Annuler ce rendez-vous ?',
    'Remove this item?': 'Supprimer cet élément ?',
    'Close this announcement?': 'Fermer cette annonce ?',
    'Open public calendar': 'Ouvrir le calendrier public',
    'Open module': 'Ouvrir le module',
    'Open file': 'Ouvrir le fichier',
    'Back': 'Retour',
    'Cancel': 'Annuler',
    'Save': 'Enregistrer',
    'Delete': 'Supprimer',
    'Remove': 'Retirer',
    'Close': 'Fermer',
    'Search': 'Recherche',
    'Language': 'Langue',
    'Home': 'Accueil',
    'Calendar': 'Calendrier',
    'Content': 'Contenu',
    'Status': 'État',
    'Profile': 'Profil',
    'Fleet management': 'Gestion de flotte',
    'Staff panel': 'Panneau staff',
  },
  es: {
    'Primary': 'Principal',
    'Account': 'Cuenta',
    'Staff quick actions': 'Acciones rápidas del equipo',
    'All categories': 'Todas las categorías',
    'All types': 'Todos los tipos',
    'All fleets': 'Todas las flotas',
    'All statuses': 'Todos los estados',
    'All roles': 'Todos los roles',
    'No slots': 'Sin espacios',
    'No summary saved.': 'No hay resumen guardado.',
    'No details saved.': 'No hay detalles guardados.',
    'No matching forum threads.': 'No hay hilos del foro coincidentes.',
    'No matching guides.': 'No hay guías coincidentes.',
    'No matching fleet announcements.': 'No hay anuncios de flota coincidentes.',
    'No upcoming appointments found.': 'No se encontraron citas próximas.',
    'No builds found.': 'No se encontraron builds.',
    'No builds yet.': 'Aún no hay builds.',
    'No guides yet.': 'Aún no hay guías.',
    'No threads yet.': 'Aún no hay hilos.',
    'No account yet?': '¿Aún no tienes cuenta?',
    'Already have an account?': '¿Ya tienes una cuenta?',
    'Create account': 'Crear cuenta',
    'Sign in': 'Iniciar sesión',
    'Login failed.': 'Error al iniciar sesión.',
    'Registration failed.': 'Error en el registro.',
    'Loading ...': 'Cargando ...',
    'Saving ...': 'Guardando ...',
    'Creating account ...': 'Creando cuenta ...',
    'Loading profile ...': 'Cargando perfil ...',
    'Profile saved.': 'Perfil guardado.',
    'Account created. You can sign in now.': 'Cuenta creada. Ya puedes iniciar sesión.',
    'Delete this build?': '¿Eliminar este build?',
    'Delete this guide?': '¿Eliminar esta guía?',
    'Cancel this appointment?': '¿Cancelar esta cita?',
    'Remove this item?': '¿Quitar este elemento?',
    'Close this announcement?': '¿Cerrar este anuncio?',
    'Open public calendar': 'Abrir calendario público',
    'Open module': 'Abrir módulo',
    'Open file': 'Abrir archivo',
    'Back': 'Volver',
    'Cancel': 'Cancelar',
    'Save': 'Guardar',
    'Delete': 'Eliminar',
    'Remove': 'Quitar',
    'Close': 'Cerrar',
    'Search': 'Buscar',
    'Language': 'Idioma',
    'Home': 'Inicio',
    'Calendar': 'Calendario',
    'Content': 'Contenido',
    'Status': 'Estado',
    'Profile': 'Perfil',
    'Fleet management': 'Gestión de flota',
    'Staff panel': 'Panel del equipo',
  },
  pt: {
    'Primary': 'Principal',
    'Account': 'Conta',
    'Staff quick actions': 'Ações rápidas da equipa',
    'All categories': 'Todas as categorias',
    'All types': 'Todos os tipos',
    'All fleets': 'Todas as frotas',
    'All statuses': 'Todos os estados',
    'All roles': 'Todas as funções',
    'No slots': 'Sem espaços',
    'No summary saved.': 'Nenhum resumo guardado.',
    'No details saved.': 'Nenhum detalhe guardado.',
    'No matching forum threads.': 'Nenhum tópico do fórum correspondente.',
    'No matching guides.': 'Nenhum guia correspondente.',
    'No matching fleet announcements.': 'Nenhum anúncio de frota correspondente.',
    'No upcoming appointments found.': 'Nenhum compromisso futuro encontrado.',
    'No builds found.': 'Nenhum build encontrado.',
    'No builds yet.': 'Ainda não há builds.',
    'No guides yet.': 'Ainda não há guias.',
    'No threads yet.': 'Ainda não há tópicos.',
    'No account yet?': 'Ainda não tem conta?',
    'Already have an account?': 'Já tem uma conta?',
    'Create account': 'Criar conta',
    'Sign in': 'Entrar',
    'Login failed.': 'Falha ao iniciar sessão.',
    'Registration failed.': 'Falha no registo.',
    'Loading ...': 'A carregar ...',
    'Saving ...': 'A guardar ...',
    'Creating account ...': 'A criar conta ...',
    'Loading profile ...': 'A carregar perfil ...',
    'Profile saved.': 'Perfil guardado.',
    'Account created. You can sign in now.': 'Conta criada. Pode iniciar sessão agora.',
    'Delete this build?': 'Eliminar este build?',
    'Delete this guide?': 'Eliminar este guia?',
    'Cancel this appointment?': 'Cancelar este compromisso?',
    'Remove this item?': 'Remover este item?',
    'Close this announcement?': 'Fechar este anúncio?',
    'Open public calendar': 'Abrir calendário público',
    'Open module': 'Abrir módulo',
    'Open file': 'Abrir ficheiro',
    'Back': 'Voltar',
    'Cancel': 'Cancelar',
    'Save': 'Guardar',
    'Delete': 'Eliminar',
    'Remove': 'Remover',
    'Close': 'Fechar',
    'Search': 'Pesquisar',
    'Language': 'Idioma',
    'Home': 'Início',
    'Calendar': 'Calendário',
    'Content': 'Conteúdo',
    'Status': 'Estado',
    'Profile': 'Perfil',
    'Fleet management': 'Gestão de frota',
    'Staff panel': 'Painel da equipa',
  },
  ru: {
    'Primary': 'Основное',
    'Account': 'Аккаунт',
    'Staff quick actions': 'Быстрые действия штаба',
    'All categories': 'Все категории',
    'All types': 'Все типы',
    'All fleets': 'Все флоты',
    'All statuses': 'Все статусы',
    'All roles': 'Все роли',
    'No slots': 'Нет слотов',
    'No summary saved.': 'Сводка не сохранена.',
    'No details saved.': 'Детали не сохранены.',
    'No matching forum threads.': 'Подходящих тем форума нет.',
    'No matching guides.': 'Подходящих гайдов нет.',
    'No matching fleet announcements.': 'Подходящих объявлений флота нет.',
    'No upcoming appointments found.': 'Предстоящие события не найдены.',
    'No builds found.': 'Билды не найдены.',
    'No builds yet.': 'Билдов пока нет.',
    'No guides yet.': 'Гайдов пока нет.',
    'No threads yet.': 'Тем пока нет.',
    'No account yet?': 'Еще нет аккаунта?',
    'Already have an account?': 'Уже есть аккаунт?',
    'Create account': 'Создать аккаунт',
    'Sign in': 'Войти',
    'Login failed.': 'Вход не выполнен.',
    'Registration failed.': 'Регистрация не удалась.',
    'Loading ...': 'Загрузка ...',
    'Saving ...': 'Сохранение ...',
    'Creating account ...': 'Создание аккаунта ...',
    'Loading profile ...': 'Загрузка профиля ...',
    'Profile saved.': 'Профиль сохранен.',
    'Account created. You can sign in now.': 'Аккаунт создан. Теперь можно войти.',
    'Delete this build?': 'Удалить этот билд?',
    'Delete this guide?': 'Удалить этот гайд?',
    'Cancel this appointment?': 'Отменить это событие?',
    'Remove this item?': 'Удалить этот элемент?',
    'Close this announcement?': 'Закрыть это объявление?',
    'Open public calendar': 'Открыть публичный календарь',
    'Open module': 'Открыть модуль',
    'Open file': 'Открыть файл',
    'Back': 'Назад',
    'Cancel': 'Отмена',
    'Save': 'Сохранить',
    'Delete': 'Удалить',
    'Remove': 'Убрать',
    'Close': 'Закрыть',
    'Search': 'Поиск',
    'Language': 'Язык',
    'Home': 'Главная',
    'Calendar': 'Календарь',
    'Content': 'Контент',
    'Status': 'Статус',
    'Profile': 'Профиль',
    'Fleet management': 'Управление флотом',
    'Staff panel': 'Панель штаба',
  },
  cn: {
    'Primary': '主要',
    'Account': '账户',
    'Staff quick actions': '管理快捷操作',
    'All categories': '所有分类',
    'All types': '所有类型',
    'All fleets': '所有舰队',
    'All statuses': '所有状态',
    'All roles': '所有角色',
    'No slots': '无槽位',
    'No summary saved.': '未保存摘要。',
    'No details saved.': '未保存详情。',
    'No matching forum threads.': '没有匹配的论坛主题。',
    'No matching guides.': '没有匹配的指南。',
    'No matching fleet announcements.': '没有匹配的舰队公告。',
    'No upcoming appointments found.': '未找到即将到来的日程。',
    'No builds found.': '未找到配装。',
    'No builds yet.': '暂无配装。',
    'No guides yet.': '暂无指南。',
    'No threads yet.': '暂无主题。',
    'No account yet?': '还没有账号？',
    'Already have an account?': '已有账号？',
    'Create account': '创建账号',
    'Sign in': '登录',
    'Login failed.': '登录失败。',
    'Registration failed.': '注册失败。',
    'Loading ...': '正在加载 ...',
    'Saving ...': '正在保存 ...',
    'Creating account ...': '正在创建账号 ...',
    'Loading profile ...': '正在加载资料 ...',
    'Profile saved.': '资料已保存。',
    'Account created. You can sign in now.': '账号已创建。现在可以登录。',
    'Delete this build?': '删除此配装？',
    'Delete this guide?': '删除此指南？',
    'Cancel this appointment?': '取消此日程？',
    'Remove this item?': '移除此项目？',
    'Close this announcement?': '关闭此公告？',
    'Open public calendar': '打开公共日历',
    'Open module': '打开模块',
    'Open file': '打开文件',
    'Back': '返回',
    'Cancel': '取消',
    'Save': '保存',
    'Delete': '删除',
    'Remove': '移除',
    'Close': '关闭',
    'Search': '搜索',
    'Language': '语言',
    'Home': '首页',
    'Calendar': '日历',
    'Content': '内容',
    'Status': '状态',
    'Profile': '个人资料',
    'Fleet management': '舰队管理',
    'Staff panel': '管理面板',
  },
}


const generatedPhraseTranslations = {
  de: {
    'Upgrade {index}': 'Upgrade {index}',
    'Administration': 'Verwaltung', 'Rate': 'Rate', 'Crew': 'Crew', 'Free': 'Frei', 'Upgrades': 'Upgrades', 'slots': 'Slots',
    'Primary navigation': 'Primäre Navigation', 'Account navigation': 'Account-Navigation', 'API online': 'API online',
    'Available now': 'Jetzt verfügbar', 'Build designer': 'Build-Designer', 'Planned': 'Geplant', 'Threads': 'Threads',
    'Balanced': 'Ausgewogen', 'Gunnery': 'Artillerie', 'Boarding': 'Entern', 'Defensive': 'Defensiv',
    'Crew {current}/{max}': 'Crew {current}/{max}', '{ammo} ammo · {consumables}/3 consumables · {hold} hold': '{ammo} Munition · {consumables}/3 Verbrauchsgüter · {hold} Laderaum',
    'Hold: {items}': 'Laderaum: {items}', 'Build name': 'Build-Name', 'Build type': 'Build-Typ', 'Rate {value}': 'Rate {value}',
    '{value}': '{value}', 'Crew {value}': 'Crew {value}', 'Crew: {current} / {max}': 'Crew: {current} / {max}', 'Free: {value}': 'Frei: {value}',
    '{count} slot(s)': '{count} Slot(s)', '{count} / {max} slot(s)': '{count} / {max} Slot(s)', 'Consumable slot {index}': 'Verbrauchsgut-Slot {index}', 'Hold slot {index}': 'Laderaum-Slot {index}',
    'Front': 'Bug', 'Rear': 'Heck', 'Starboard': 'Steuerbord', 'Sail': 'Segel', 'Crew distribution': 'Crew-Verteilung',
    'Admin access': 'Admin-Zugang', 'Sign in': 'Anmelden', 'Signing in ...': 'Anmeldung ...', 'Administration': 'Verwaltung', 'Admin login required': 'Admin-Login erforderlich', 'Admin sections': 'Admin-Bereiche',
    'API connection': 'API-Verbindung', 'The backend responded successfully.': 'Das Backend hat erfolgreich geantwortet.', 'PvE Farming': 'PvE-Farming', 'PvP Arena': 'PvP-Arena',
    'Video': 'Video', 'Text': 'Text', 'Thread': 'Thread', 'Training': 'Training', 'Operation': 'Operation', 'Details': 'Details', 'Status': 'Status',
  },
  fr: {
    'Description': 'Description',
    'Combat': 'Combat',
    '1 guide': '1 guide',
    '{count} guides': '{count} guides',
    'Publish guide': 'Publier le guide',
    'Guide text': 'Texte du guide',
    'Today': 'Aujourd’hui',
    'Month': 'Mois',
    'Selected day': 'Jour sélectionné',
    'Recon': 'Reconnaissance',
    'Mixed': 'Mixte',
    'Active': 'Actif',
    'Send application': 'Envoyer la candidature',
    'Application could not be submitted.': 'La candidature n’a pas pu être envoyée.',
    'Approve': 'Approuver',
    'Reject': 'Refuser',
    'Activate': 'Activer',
    'Deactivate': 'Désactiver',
    'Reactivate': 'Réactiver',
    'Applications': 'Candidatures',
    'Rate': 'Rang', 'Type': 'Type', 'Free': 'Libre', 'slots': 'emplacements', 'Primary navigation': 'Navigation principale', 'Account navigation': 'Navigation du compte', 'Announcements': 'Annonces',
    'Available now': 'Disponible maintenant', 'Build designer': 'Concepteur de build', 'Planned': 'Planifié', 'Announcement board': 'Tableau d’annonces', 'Public board': 'Tableau public', 'Leader notes': 'Notes du chef', 'Own posts': 'Vos publications',
    'Community board': 'Tableau communautaire', 'Threads': 'Fils', 'Knowledge base': 'Base de connaissances', 'Month view': 'Vue mensuelle',
    'Balanced': 'Équilibré', 'Gunnery': 'Artillerie', 'Boarding': 'Abordage', 'Defensive': 'Défensif', '{used}/{max} upgrades': '{used}/{max} améliorations',
    '{ammo} ammo · {consumables}/3 consumables · {hold} hold': '{ammo} munitions · {consumables}/3 consommables · {hold} cale', 'Hold: {items}': 'Cale : {items}', '{count} weapons': '{count} armes', '{count} special crew': '{count} équipage spécial', 'Special crew: {items}': 'Équipage spécial : {items}',
    'Build name': 'Nom du build', 'Build type': 'Type de build', 'Rate {value}': 'Rang {value}', '{value}': '{value}', '{count} upgrades': '{count} améliorations', '{value} weapons': '{value} armes', '{value} special crew': '{value} équipage spécial',
    'Special crew': 'Équipage spécial', 'Sail': 'Voile', 'Locked: needs unlock upgrade': 'Verrouillé : amélioration de déverrouillage requise', 'Free: {value}': 'Libre : {value}', '{count} slot(s)': '{count} emplacement(s)', '{count} / {max} slot(s)': '{count} / {max} emplacement(s)',
    'Consumable slot {index}': 'Emplacement consommable {index}', 'Hold slot {index}': 'Emplacement de cale {index}', 'Front': 'Avant', 'Rear': 'Arrière', 'Starboard': 'Tribord', 'Front weapon slot {index}': 'Emplacement d’arme avant {index}', 'Rear weapon slot {index}': 'Emplacement d’arme arrière {index}', 'Starboard weapon slot {index}': 'Emplacement d’arme tribord {index}', 'Special crew slot {index}': 'Emplacement équipage spécial {index}',
    '{upgrades}/{max} upgrades · {free} free crew': '{upgrades}/{max} améliorations · {free} équipage libre', 'Front weapons': 'Armes avant', 'Rear weapons': 'Armes arrière', 'Starboard weapons': 'Armes tribord',
    'API connection': 'Connexion API', 'The backend responded successfully.': 'Le backend a répondu avec succès.', '1 build': '1 build', '{count} builds': '{count} builds', 'Content could not be removed.': 'Le contenu n’a pas pu être retiré.', 'Announcement could not be closed.': 'L’annonce n’a pas pu être fermée.',
    'Announcement': 'Annonce', 'Focus': 'Focus', 'Leader': 'Chef', 'Guests': 'Invités', 'Expectations': 'Attentes', 'Activity plan': 'Plan d’activité', 'Contact note': 'Note de contact', 'New announcement': 'Nouvelle annonce', 'Group filters': 'Filtres de groupe', 'Rates {max}–{min}': 'Rangs {max}–{min}', 'Guests allowed': 'Invités autorisés', 'Leader: {name}': 'Chef : {name}', '{count} spots left': '{count} places restantes', 'Announcement mode': 'Mode annonce', 'Post announcement': 'Publier l’annonce', 'Any': 'Tous', 'spots left': 'places restantes', 'Guest': 'Invité', 'rates {max}–{min}': 'rangs {max}–{min}', 'allowed: {requirement}': 'autorisé : {requirement}', 'Leader announcement': 'Annonce du chef', 'Announcement overview': 'Aperçu de l’annonce', 'Activity plan': 'Plan d’activité', 'Contact': 'Contact', 'My announcements': 'Mes annonces', '1 own announcement': '1 annonce personnelle', '{count} own announcements': '{count} annonces personnelles', 'Your announcements': 'Vos annonces',
    'Upload media': 'Téléverser un média', 'File could not be uploaded.': 'Le fichier n’a pas pu être téléversé.', 'Image': 'Image', 'Video': 'Vidéo', 'Text': 'Texte', 'File': 'Fichier', 'Last activity: {value}': 'Dernière activité : {value}', 'Write your first post ...': 'Écrivez votre premier message ...', 'Thread': 'Fil', 'First post': 'Premier message',
    'Operation': 'Opération', 'Location': 'Lieu', 'Start date': 'Date de début', 'Start time': 'Heure de début', 'End date': 'Date de fin', 'End time': 'Heure de fin', 'Month navigation': 'Navigation mensuelle',
  },
  es: {
    '1 build': '1 build',
    '{count} builds': '{count} builds',
    'General': 'General',
    'Today': 'Hoy',
    'Month': 'Mes',
    'Selected day': 'Día seleccionado',
    'Recon': 'Reconocimiento',
    'Mixed': 'Mixto',
    'Active': 'Activo',
    'Send application': 'Enviar solicitud',
    'Application could not be submitted.': 'No se pudo enviar la solicitud.',
    'Approve': 'Aprobar',
    'Reject': 'Rechazar',
    'Activate': 'Activar',
    'Deactivate': 'Desactivar',
    'Reactivate': 'Reactivar',
    'Applications': 'Solicitudes',
    'Rate': 'Rango', 'Free': 'Libre', 'slots': 'espacios', 'Primary navigation': 'Navegación principal', 'Account navigation': 'Navegación de cuenta', 'Announcements': 'Anuncios',
    'Available now': 'Disponible ahora', 'Build designer': 'Diseñador de builds', 'Planned': 'Planificado', 'Announcement board': 'Tablero de anuncios', 'Leader notes': 'Notas del líder', 'Own posts': 'Publicaciones propias', 'Community board': 'Tablero comunitario', 'Threads': 'Hilos', 'Knowledge base': 'Base de conocimiento', 'Month view': 'Vista mensual',
    'Balanced': 'Equilibrado', 'Gunnery': 'Artillería', 'Defensive': 'Defensivo', '{used}/{max} upgrades': '{used}/{max} mejoras', '{ammo} ammo · {consumables}/3 consumables · {hold} hold': '{ammo} munición · {consumables}/3 consumibles · {hold} bodega', 'Hold: {items}': 'Bodega: {items}', '{count} weapons': '{count} armas', '{count} special crew': '{count} tripulación especial', 'Special crew: {items}': 'Tripulación especial: {items}',
    'Build name': 'Nombre del build', 'Build type': 'Tipo de build', 'Rate {value}': 'Rango {value}', '{value}': '{value}', '{count} upgrades': '{count} mejoras', '{value} weapons': '{value} armas', '{value} special crew': '{value} tripulación especial', 'Special crew': 'Tripulación especial', 'Sail': 'Vela', 'Locked: needs unlock upgrade': 'Bloqueado: requiere mejora de desbloqueo', 'Free: {value}': 'Libre: {value}', '{count} slot(s)': '{count} espacio(s)', '{count} / {max} slot(s)': '{count} / {max} espacio(s)', 'Consumable slot {index}': 'Espacio de consumible {index}', 'Hold slot {index}': 'Espacio de bodega {index}', 'Front': 'Proa', 'Rear': 'Popa', 'Starboard': 'Estribor', 'Front weapon slot {index}': 'Espacio de arma de proa {index}', 'Rear weapon slot {index}': 'Espacio de arma de popa {index}', 'Starboard weapon slot {index}': 'Espacio de arma de estribor {index}', 'Special crew slot {index}': 'Espacio de tripulación especial {index}', '{upgrades}/{max} upgrades · {free} free crew': '{upgrades}/{max} mejoras · {free} tripulación libre', 'Front weapons': 'Armas de proa', 'Rear weapons': 'Armas de popa', 'Starboard weapons': 'Armas de estribor',
    'API connection': 'Conexión API', 'The backend responded successfully.': 'El backend respondió correctamente.', 'Content could not be removed.': 'No se pudo quitar el contenido.', 'Announcement could not be closed.': 'No se pudo cerrar el anuncio.',
    'Announcement': 'Anuncio', 'Focus': 'Enfoque', 'Leader': 'Líder', 'Guests': 'Invitados', 'Expectations': 'Expectativas', 'Activity plan': 'Plan de actividad', 'Contact note': 'Nota de contacto', 'New announcement': 'Nuevo anuncio', 'Group filters': 'Filtros de grupo', 'Rates {max}–{min}': 'Rangos {max}–{min}', 'Guests allowed': 'Invitados permitidos', 'Leader: {name}': 'Líder: {name}', '{count} spots left': '{count} plazas restantes', 'Announcement mode': 'Modo anuncio', 'Post announcement': 'Publicar anuncio', 'Any': 'Cualquiera', 'spots left': 'plazas restantes', 'Guest': 'Invitado', 'rates {max}–{min}': 'rangos {max}–{min}', 'allowed: {requirement}': 'permitido: {requirement}', 'Leader announcement': 'Anuncio del líder', 'Announcement overview': 'Resumen del anuncio', 'Activity plan': 'Plan de actividad', 'Contact': 'Contacto', 'My announcements': 'Mis anuncios', '1 own announcement': '1 anuncio propio', '{count} own announcements': '{count} anuncios propios', 'Your announcements': 'Tus anuncios',
    'Upload media': 'Subir medios', 'File could not be uploaded.': 'No se pudo subir el archivo.', 'Image': 'Imagen', 'Video': 'Vídeo', 'Text': 'Texto', 'File': 'Archivo', 'Last activity: {value}': 'Última actividad: {value}', 'Write your first post ...': 'Escribe tu primera publicación ...', 'Thread': 'Hilo', 'First post': 'Primera publicación',
    'Operation': 'Operación', 'Location': 'Ubicación', 'Start date': 'Fecha de inicio', 'Start time': 'Hora de inicio', 'End date': 'Fecha de fin', 'End time': 'Hora de fin', 'Month navigation': 'Navegación mensual',
  },
  pt: {
    '1 build': '1 build',
    '{count} builds': '{count} builds',
    'Today': 'Hoje',
    'Month': 'Mês',
    'Selected day': 'Dia selecionado',
    'Recon': 'Reconhecimento',
    'Mixed': 'Misto',
    'Active': 'Ativo',
    'Send application': 'Enviar candidatura',
    'Application could not be submitted.': 'A candidatura não pôde ser enviada.',
    'Approve': 'Aprovar',
    'Reject': 'Rejeitar',
    'Activate': 'Ativar',
    'Deactivate': 'Desativar',
    'Reactivate': 'Reativar',
    'Applications': 'Candidaturas',
    'Rate': 'Nível', 'Free': 'Livre', 'slots': 'espaços', 'Primary navigation': 'Navegação principal', 'Account navigation': 'Navegação da conta', 'Announcements': 'Anúncios',
    'Available now': 'Disponível agora', 'Build designer': 'Designer de builds', 'Planned': 'Planeado', 'Announcement board': 'Quadro de anúncios', 'Leader notes': 'Notas do líder', 'Own posts': 'Publicações próprias', 'Community board': 'Quadro da comunidade', 'Threads': 'Tópicos', 'Knowledge base': 'Base de conhecimento', 'Month view': 'Vista mensal',
    'Balanced': 'Equilibrado', 'Gunnery': 'Artilharia', 'Defensive': 'Defensivo', '{used}/{max} upgrades': '{used}/{max} melhorias', '{ammo} ammo · {consumables}/3 consumables · {hold} hold': '{ammo} munição · {consumables}/3 consumíveis · {hold} porão', 'Hold: {items}': 'Porão: {items}', '{count} weapons': '{count} armas', '{count} special crew': '{count} tripulação especial', 'Special crew: {items}': 'Tripulação especial: {items}',
    'Build name': 'Nome do build', 'Build type': 'Tipo de build', 'Rate {value}': 'Nível {value}', '{value}': '{value}', '{count} upgrades': '{count} melhorias', '{value} weapons': '{value} armas', '{value} special crew': '{value} tripulação especial', 'Special crew': 'Tripulação especial', 'Sail': 'Vela', 'Locked: needs unlock upgrade': 'Bloqueado: requer melhoria de desbloqueio', 'Free: {value}': 'Livre: {value}', '{count} slot(s)': '{count} espaço(s)', '{count} / {max} slot(s)': '{count} / {max} espaço(s)', 'Consumable slot {index}': 'Espaço de consumível {index}', 'Hold slot {index}': 'Espaço de porão {index}', 'Front': 'Proa', 'Rear': 'Popa', 'Starboard': 'Estibordo', 'Front weapon slot {index}': 'Espaço de arma frontal {index}', 'Rear weapon slot {index}': 'Espaço de arma traseira {index}', 'Starboard weapon slot {index}': 'Espaço de arma de estibordo {index}', 'Special crew slot {index}': 'Espaço de tripulação especial {index}', '{upgrades}/{max} upgrades · {free} free crew': '{upgrades}/{max} melhorias · {free} tripulação livre', 'Front weapons': 'Armas de proa', 'Rear weapons': 'Armas de popa', 'Starboard weapons': 'Armas de estibordo',
    'API connection': 'Ligação API', 'The backend responded successfully.': 'O backend respondeu com sucesso.', 'Content could not be removed.': 'O conteúdo não pôde ser removido.', 'Announcement could not be closed.': 'O anúncio não pôde ser fechado.',
    'Announcement': 'Anúncio', 'Focus': 'Foco', 'Leader': 'Líder', 'Guests': 'Convidados', 'Expectations': 'Expectativas', 'Activity plan': 'Plano de atividade', 'Contact note': 'Nota de contacto', 'New announcement': 'Novo anúncio', 'Group filters': 'Filtros de grupo', 'Rates {max}–{min}': 'Níveis {max}–{min}', 'Guests allowed': 'Convidados permitidos', 'Leader: {name}': 'Líder: {name}', '{count} spots left': '{count} vagas restantes', 'Announcement mode': 'Modo anúncio', 'Post announcement': 'Publicar anúncio', 'Any': 'Qualquer', 'spots left': 'vagas restantes', 'Guest': 'Convidado', 'rates {max}–{min}': 'níveis {max}–{min}', 'allowed: {requirement}': 'permitido: {requirement}', 'Leader announcement': 'Anúncio do líder', 'Announcement overview': 'Visão geral do anúncio', 'Activity plan': 'Plano de atividade', 'Contact': 'Contacto', 'My announcements': 'Meus anúncios', '1 own announcement': '1 anúncio próprio', '{count} own announcements': '{count} anúncios próprios', 'Your announcements': 'Os seus anúncios',
    'Upload media': 'Carregar mídia', 'File could not be uploaded.': 'O ficheiro não pôde ser carregado.', 'Image': 'Imagem', 'Video': 'Vídeo', 'Text': 'Texto', 'File': 'Ficheiro', 'Last activity: {value}': 'Última atividade: {value}', 'Write your first post ...': 'Escreva a sua primeira publicação ...', 'Thread': 'Tópico', 'First post': 'Primeira publicação',
    'Operation': 'Operação', 'Location': 'Localização', 'Start date': 'Data de início', 'Start time': 'Hora de início', 'End date': 'Data de fim', 'End time': 'Hora de fim', 'Month navigation': 'Navegação mensal',
  },
  ru: {
    'Today': 'Сегодня',
    'Month': 'Месяц',
    'Selected day': 'Выбранный день',
    'Recon': 'Разведка',
    'Mixed': 'Смешанный',
    'Active': 'Активно',
    'Send application': 'Отправить заявку',
    'Application could not be submitted.': 'Не удалось отправить заявку.',
    'Approve': 'Одобрить',
    'Reject': 'Отклонить',
    'Activate': 'Активировать',
    'Deactivate': 'Деактивировать',
    'Reactivate': 'Повторно активировать',
    'Applications': 'Заявки',
    'Rate': 'Ранг', 'Free': 'Свободно', 'slots': 'слоты', 'Primary navigation': 'Основная навигация', 'Account navigation': 'Навигация аккаунта', 'Announcements': 'Объявления',
    'Available now': 'Доступно сейчас', 'Build designer': 'Конструктор билдов', 'Planned': 'Запланировано', 'Announcement board': 'Доска объявлений', 'Leader notes': 'Заметки лидера', 'Own posts': 'Собственные записи', 'Community board': 'Доска сообщества', 'Threads': 'Темы', 'Knowledge base': 'База знаний', 'Month view': 'Месячный вид',
    'Balanced': 'Сбалансированный', 'Gunnery': 'Артиллерия', 'Defensive': 'Оборонительный', '{used}/{max} upgrades': '{used}/{max} улучшений', '{ammo} ammo · {consumables}/3 consumables · {hold} hold': '{ammo} боеприпасов · {consumables}/3 расходников · {hold} трюм', 'Hold: {items}': 'Трюм: {items}', '{count} weapons': '{count} оружия', '{count} special crew': '{count} спецэкипажа', 'Special crew: {items}': 'Спецэкипаж: {items}',
    'Build name': 'Название билда', 'Build type': 'Тип билда', 'Rate {value}': 'Ранг {value}', '{value}': '{value}', '{count} upgrades': '{count} улучшений', '{value} weapons': '{value} оружия', '{value} special crew': '{value} спецэкипажа', 'Special crew': 'Спецэкипаж', 'Sail': 'Парус', 'Locked: needs unlock upgrade': 'Заблокировано: нужно разблокирующее улучшение', 'Free: {value}': 'Свободно: {value}', '{count} slot(s)': '{count} слот(ов)', '{count} / {max} slot(s)': '{count} / {max} слот(ов)', 'Consumable slot {index}': 'Слот расходника {index}', 'Hold slot {index}': 'Слот трюма {index}', 'Front': 'Нос', 'Rear': 'Корма', 'Starboard': 'Правый борт', 'Front weapon slot {index}': 'Слот носового оружия {index}', 'Rear weapon slot {index}': 'Слот кормового оружия {index}', 'Starboard weapon slot {index}': 'Слот оружия правого борта {index}', 'Special crew slot {index}': 'Слот спецэкипажа {index}', '{upgrades}/{max} upgrades · {free} free crew': '{upgrades}/{max} улучшений · {free} свободного экипажа', 'Front weapons': 'Носовое оружие', 'Rear weapons': 'Кормовое оружие', 'Starboard weapons': 'Оружие правого борта',
    'API connection': 'Соединение API', 'The backend responded successfully.': 'Бэкенд ответил успешно.', 'Content could not be removed.': 'Не удалось удалить контент.', 'Announcement could not be closed.': 'Не удалось закрыть объявление.',
    'Announcement': 'Объявление', 'Focus': 'Фокус', 'Leader': 'Лидер', 'Guests': 'Гости', 'Expectations': 'Ожидания', 'Activity plan': 'План активности', 'Contact note': 'Контактная заметка', 'New announcement': 'Новое объявление', 'Group filters': 'Фильтры групп', 'Rates {max}–{min}': 'Ранги {max}–{min}', 'Guests allowed': 'Гости разрешены', 'Leader: {name}': 'Лидер: {name}', '{count} spots left': 'осталось мест: {count}', 'Announcement mode': 'Режим объявления', 'Post announcement': 'Опубликовать объявление', 'Any': 'Любой', 'spots left': 'мест осталось', 'Guest': 'Гость', 'rates {max}–{min}': 'ранги {max}–{min}', 'allowed: {requirement}': 'разрешено: {requirement}', 'Leader announcement': 'Объявление лидера', 'Announcement overview': 'Обзор объявления', 'Activity plan': 'План активности', 'Contact': 'Контакт', 'My announcements': 'Мои объявления', '1 own announcement': '1 собственное объявление', '{count} own announcements': '{count} собственных объявлений', 'Your announcements': 'Ваши объявления',
    'Upload media': 'Загрузить медиа', 'File could not be uploaded.': 'Не удалось загрузить файл.', 'Image': 'Изображение', 'Video': 'Видео', 'Text': 'Текст', 'File': 'Файл', 'Last activity: {value}': 'Последняя активность: {value}', 'Write your first post ...': 'Напишите первое сообщение ...', 'Thread': 'Тема', 'First post': 'Первое сообщение',
    'Operation': 'Операция', 'Location': 'Локация', 'Start date': 'Дата начала', 'Start time': 'Время начала', 'End date': 'Дата окончания', 'End time': 'Время окончания', 'Month navigation': 'Навигация по месяцам',
  },
  cn: {
    'Today': '今天',
    'Month': '月份',
    'Selected day': '选中日期',
    'Recon': '侦察',
    'Mixed': '混合',
    'Active': '活跃',
    'Send application': '发送申请',
    'Application could not be submitted.': '无法提交申请。',
    'Approve': '批准',
    'Reject': '拒绝',
    'Activate': '启用',
    'Deactivate': '停用',
    'Reactivate': '重新启用',
    'Applications': '申请',
    'Rate': '等级', 'Free': '空闲', 'slots': '槽位', 'Primary navigation': '主导航', 'Account navigation': '账户导航', 'Announcements': '公告',
    'Available now': '现在可用', 'Build designer': '配装设计器', 'Planned': '计划中', 'Announcement board': '公告板', 'Leader notes': '队长备注', 'Own posts': '自己的帖子', 'Community board': '社区板块', 'Threads': '主题', 'Knowledge base': '知识库', 'Month view': '月视图',
    'Balanced': '均衡', 'Gunnery': '炮术', 'Defensive': '防御', '{used}/{max} upgrades': '{used}/{max} 升级', '{ammo} ammo · {consumables}/3 consumables · {hold} hold': '{ammo} 弹药 · {consumables}/3 消耗品 · {hold} 货舱', 'Hold: {items}': '货舱：{items}', '{count} weapons': '{count} 武器', '{count} special crew': '{count} 特殊船员', 'Special crew: {items}': '特殊船员：{items}',
    'Build name': '配装名称', 'Build type': '配装类型', 'Rate {value}': '等级 {value}', '{value}': '{value}', '{count} upgrades': '{count} 升级', '{value} weapons': '{value} 武器', '{value} special crew': '{value} 特殊船员', 'Special crew': '特殊船员', 'Sail': '帆', 'Locked: needs unlock upgrade': '已锁定：需要解锁升级', 'Free: {value}': '空闲：{value}', '{count} slot(s)': '{count} 个槽位', '{count} / {max} slot(s)': '{count} / {max} 个槽位', 'Consumable slot {index}': '消耗品槽位 {index}', 'Hold slot {index}': '货舱槽位 {index}', 'Front': '船首', 'Rear': '船尾', 'Starboard': '右舷', 'Front weapon slot {index}': '船首武器槽位 {index}', 'Rear weapon slot {index}': '船尾武器槽位 {index}', 'Starboard weapon slot {index}': '右舷武器槽位 {index}', 'Special crew slot {index}': '特殊船员槽位 {index}', '{upgrades}/{max} upgrades · {free} free crew': '{upgrades}/{max} 升级 · {free} 空闲船员', 'Front weapons': '船首武器', 'Rear weapons': '船尾武器', 'Starboard weapons': '右舷武器',
    'API connection': 'API 连接', 'The backend responded successfully.': '后端响应成功。', 'Content could not be removed.': '无法移除内容。', 'Announcement could not be closed.': '无法关闭公告。',
    'Announcement': '公告', 'Focus': '重点', 'Leader': '队长', 'Guests': '访客', 'Expectations': '期望', 'Activity plan': '活动计划', 'Contact note': '联系备注', 'New announcement': '新公告', 'Group filters': '小组筛选', 'Rates {max}–{min}': '等级 {max}–{min}', 'Guests allowed': '允许访客', 'Leader: {name}': '队长：{name}', '{count} spots left': '剩余 {count} 个名额', 'Announcement mode': '公告模式', 'Post announcement': '发布公告', 'Any': '任意', 'spots left': '剩余名额', 'Guest': '访客', 'rates {max}–{min}': '等级 {max}–{min}', 'allowed: {requirement}': '允许：{requirement}', 'Leader announcement': '队长公告', 'Announcement overview': '公告概览', 'Activity plan': '活动计划', 'Contact': '联系', 'My announcements': '我的公告', '1 own announcement': '1 条自己的公告', '{count} own announcements': '{count} 条自己的公告', 'Your announcements': '你的公告',
    'Upload media': '上传媒体', 'File could not be uploaded.': '无法上传文件。', 'Image': '图片', 'Video': '视频', 'Text': '文本', 'File': '文件', 'Last activity: {value}': '最后活动：{value}', 'Write your first post ...': '撰写你的第一篇帖子 ...', 'Thread': '主题', 'First post': '首帖',
    'Operation': '行动', 'Location': '地点', 'Start date': '开始日期', 'Start time': '开始时间', 'End date': '结束日期', 'End time': '结束时间', 'Month navigation': '月份导航',
  },
}

const termTranslations = {
  de: [
    ['Fleet announcements', 'Flottenankündigungen'], ['fleet announcements', 'Flottenankündigungen'], ['Fleet calendar', 'Flottenkalender'], ['fleet calendar', 'Flottenkalender'], ['Fleet management', 'Flottenverwaltung'], ['fleet management', 'Flottenverwaltung'], ['Build Manager', 'Build-Manager'], ['Build management', 'Build-Verwaltung'], ['New appointment', 'Neuer Termin'], ['New thread', 'Neuer Thread'], ['New guide', 'Neuer Guide'], ['New build', 'Neuer Build'], ['Main navigation', 'Hauptnavigation'], ['Admin panel', 'Admin-Panel'], ['Staff panel', 'Team-Panel'], ['Calendar operations', 'Kalenderverwaltung'], ['Content moderation', 'Content-Moderation'], ['System status', 'Systemstatus'], ['Guide management', 'Guide-Verwaltung'], ['Create account', 'Account erstellen'], ['Display name', 'Anzeigename'], ['Planned fleet', 'Geplante Flotte'], ['Application note', 'Bewerbungsnotiz'], ['User guides', 'User-Guides'], ['Media embeds', 'Medien-Einbettungen'], ['File embeds', 'Datei-Einbettungen'], ['Search by', 'Suchen nach'], ['Loading', 'Lade'], ['Saving', 'Speichere'], ['Posting', 'Veröffentliche'], ['Publishing', 'Veröffentliche'], ['Checking', 'Prüfe'], ['Waiting for', 'Warte auf'], ['could not be loaded', 'konnte nicht geladen werden'], ['could not be saved', 'konnte nicht gespeichert werden'], ['could not be deleted', 'konnte nicht gelöscht werden'], ['could not be created', 'konnte nicht erstellt werden'], ['could not be posted', 'konnte nicht veröffentlicht werden'], ['could not be published', 'konnte nicht veröffentlicht werden'], ['could not be cancelled', 'konnte nicht abgesagt werden'], ['could not be reached', 'konnte nicht erreicht werden'], ['failed', 'fehlgeschlagen'], ['found', 'gefunden'], ['saved', 'gespeichert'], ['created', 'erstellt'], ['deleted', 'gelöscht'], ['cancelled', 'abgesagt'], ['open', 'öffnen'], ['Open', 'Öffnen'], ['Delete', 'Löschen'], ['Remove', 'Entfernen'], ['Cancel', 'Abbrechen'], ['Close', 'Schließen'], ['Save', 'Speichern'], ['Create', 'Erstellen'], ['Search', 'Suchen'], ['Loading', 'Laden'], ['All', 'Alle'], ['No', 'Keine'], ['None', 'Keine'], ['Forum threads', 'Forum-Threads'], ['thread', 'Thread'], ['threads', 'Threads'], ['Guides', 'Guides'], ['Guide', 'Guide'], ['guide', 'Guide'], ['Builds', 'Builds'], ['builds', 'Builds'], ['build', 'Build'], ['Fleet', 'Flotte'], ['fleet', 'Flotte'], ['Fleets', 'Flotten'], ['fleets', 'Flotten'], ['Members', 'Mitglieder'], ['members', 'Mitglieder'], ['Member', 'Mitglied'], ['member', 'Mitglied'], ['Profile', 'Profil'], ['profile', 'Profil'], ['Calendar', 'Kalender'], ['calendar', 'Kalender'], ['Appointment', 'Termin'], ['appointment', 'Termin'], ['Event', 'Termin'], ['event', 'Termin'], ['Category', 'Kategorie'], ['category', 'Kategorie'], ['Categories', 'Kategorien'], ['categories', 'Kategorien'], ['Status', 'Status'], ['status', 'Status'], ['Role', 'Rolle'], ['role', 'Rolle'], ['Title', 'Titel'], ['title', 'Titel'], ['Description', 'Beschreibung'], ['description', 'Beschreibung'], ['Details', 'Details'], ['details', 'Details'], ['Summary', 'Zusammenfassung'], ['summary', 'Zusammenfassung'], ['Attachments', 'Anhänge'], ['attachments', 'Anhänge'], ['Files', 'Dateien'], ['files', 'Dateien'], ['User', 'Nutzer'], ['user', 'Nutzer'], ['Users', 'Nutzer'], ['users', 'Nutzer'], ['Moderator', 'Moderator'], ['moderator', 'Moderator'], ['Password', 'Passwort'], ['password', 'Passwort'], ['Username', 'Nutzername'], ['username', 'Nutzername'], ['Language', 'Sprache'], ['Home', 'Start'], ['Back', 'Zurück'], ['Empty', 'Leer'], ['Type', 'Typ'], ['Quantity', 'Anzahl'], ['Sailors', 'Matrosen'], ['Musketeers', 'Musketiere'], ['Soldiers', 'Soldaten'], ['Mercenaries', 'Söldner'], ['Ammunition', 'Munition'], ['Consumables', 'Verbrauchsgüter'], ['Inventory', 'Inventar'], ['Sails', 'Segel'], ['Lantern', 'Laterne'], ['Upgrade', 'Upgrade'], ['Upgrades', 'Upgrades'], ['Weapons', 'Waffen'], ['Crew', 'Crew'], ['Ship', 'Schiff'], ['ship', 'Schiff'], ['Ships', 'Schiffe'], ['ships', 'Schiffe'], ['Trade', 'Handel'], ['Trading', 'Handel'], ['Training', 'Training'], ['Support', 'Support'], ['Other', 'Sonstiges'], ['General', 'Allgemein'], ['Economy', 'Wirtschaft'], ['Combat', 'Kampf'], ['Events', 'Events'], ['Online', 'online'], ['offline', 'offline'], ['active', 'aktiv'], ['pending', 'offen'], ['inactive', 'inaktiv'], ['Public', 'Öffentlich'], ['public', 'öffentlich'], ['Login', 'Anmelden'], ['logout', 'abmelden'], ['Logout', 'Abmelden'], ['Register', 'Registrieren'], ['register', 'registrieren'], ['Reply', 'Antwort'], ['reply', 'Antwort'], ['Replies', 'Antworten'], ['replies', 'Antworten'], ['by', 'von'], ['and', 'und'], ['or', 'oder'], ['with', 'mit'], ['for', 'für'], ['from', 'aus'], ['in', 'in'], ['to', 'zu'], ['of', 'von'], ['the', 'die'], ['a ', 'ein '], ['an ', 'ein '],
  ],
  fr: [
    ['Fleet announcements', 'Annonces de flotte'], ['fleet announcements', 'annonces de flotte'], ['Fleet calendar', 'Calendrier de flotte'], ['fleet calendar', 'calendrier de flotte'], ['Fleet management', 'Gestion de flotte'], ['fleet management', 'gestion de flotte'], ['Build Manager', 'Gestionnaire de builds'], ['Build management', 'Gestion des builds'], ['New appointment', 'Nouveau rendez-vous'], ['New thread', 'Nouveau fil'], ['New guide', 'Nouveau guide'], ['New build', 'Nouveau build'], ['Main navigation', 'Navigation principale'], ['Admin panel', 'Panneau admin'], ['Staff panel', 'Panneau staff'], ['Calendar operations', 'Opérations calendrier'], ['Content moderation', 'Modération du contenu'], ['System status', 'État du système'], ['Guide management', 'Gestion du guide'], ['Display name', 'Nom affiché'], ['Planned fleet', 'Flotte planifiée'], ['Application note', 'Note de candidature'], ['User guides', 'Guides utilisateur'], ['Media embeds', 'Médias intégrés'], ['File embeds', 'Fichiers intégrés'], ['Search by', 'Rechercher par'], ['Loading', 'Chargement'], ['Saving', 'Enregistrement'], ['Posting', 'Publication'], ['Publishing', 'Publication'], ['Checking', 'Vérification'], ['Waiting for', 'En attente de'], ['could not be loaded', 'n’a pas pu être chargé'], ['could not be saved', 'n’a pas pu être enregistré'], ['could not be deleted', 'n’a pas pu être supprimé'], ['could not be created', 'n’a pas pu être créé'], ['could not be posted', 'n’a pas pu être publié'], ['could not be published', 'n’a pas pu être publié'], ['could not be cancelled', 'n’a pas pu être annulé'], ['could not be reached', 'n’a pas pu être joint'], ['failed', 'a échoué'], ['found', 'trouvé'], ['saved', 'enregistré'], ['created', 'créé'], ['deleted', 'supprimé'], ['cancelled', 'annulé'], ['Open', 'Ouvrir'], ['open', 'ouvrir'], ['Delete', 'Supprimer'], ['Remove', 'Retirer'], ['Cancel', 'Annuler'], ['Close', 'Fermer'], ['Save', 'Enregistrer'], ['Create', 'Créer'], ['Search', 'Rechercher'], ['All', 'Tous'], ['No', 'Aucun'], ['None', 'Aucun'], ['Forum threads', 'Fils du forum'], ['threads', 'fils'], ['thread', 'fil'], ['Guide', 'Guide'], ['guide', 'guide'], ['Builds', 'Builds'], ['builds', 'builds'], ['build', 'build'], ['Fleets', 'Flottes'], ['fleets', 'flottes'], ['Fleet', 'Flotte'], ['fleet', 'flotte'], ['Members', 'Membres'], ['members', 'membres'], ['Member', 'Membre'], ['member', 'membre'], ['Profile', 'Profil'], ['profile', 'profil'], ['Calendar', 'Calendrier'], ['calendar', 'calendrier'], ['Appointment', 'Rendez-vous'], ['appointment', 'rendez-vous'], ['Event', 'Événement'], ['event', 'événement'], ['Category', 'Catégorie'], ['category', 'catégorie'], ['Categories', 'Catégories'], ['categories', 'catégories'], ['Status', 'État'], ['status', 'état'], ['Role', 'Rôle'], ['role', 'rôle'], ['Title', 'Titre'], ['title', 'titre'], ['Description', 'Description'], ['description', 'description'], ['Details', 'Détails'], ['details', 'détails'], ['Summary', 'Résumé'], ['summary', 'résumé'], ['Attachments', 'Pièces jointes'], ['attachments', 'pièces jointes'], ['Files', 'Fichiers'], ['files', 'fichiers'], ['User', 'Utilisateur'], ['user', 'utilisateur'], ['Users', 'Utilisateurs'], ['users', 'utilisateurs'], ['Moderator', 'Modérateur'], ['moderator', 'modérateur'], ['Password', 'Mot de passe'], ['password', 'mot de passe'], ['Username', 'Nom d’utilisateur'], ['username', 'nom d’utilisateur'], ['Language', 'Langue'], ['Home', 'Accueil'], ['Back', 'Retour'], ['Empty', 'Vide'], ['Type', 'Type'], ['Quantity', 'Quantité'], ['Sailors', 'Marins'], ['Musketeers', 'Mousquetaires'], ['Soldiers', 'Soldats'], ['Mercenaries', 'Mercenaires'], ['Ammunition', 'Munitions'], ['Consumables', 'Consommables'], ['Inventory', 'Inventaire'], ['Sails', 'Voiles'], ['Lantern', 'Lanterne'], ['Upgrade', 'Amélioration'], ['Upgrades', 'Améliorations'], ['Weapons', 'Armes'], ['Crew', 'Équipage'], ['Ships', 'Navires'], ['ships', 'navires'], ['Ship', 'Navire'], ['ship', 'navire'], ['Trade', 'Commerce'], ['Trading', 'Commerce'], ['Training', 'Entraînement'], ['Support', 'Support'], ['Other', 'Autre'], ['General', 'Général'], ['Economy', 'Économie'], ['Combat', 'Combat'], ['Events', 'Événements'], ['Online', 'en ligne'], ['offline', 'hors ligne'], ['active', 'actif'], ['pending', 'en attente'], ['inactive', 'inactif'], ['Public', 'Public'], ['public', 'public'], ['Login', 'Connexion'], ['logout', 'déconnexion'], ['Logout', 'Déconnexion'], ['Register', 'Inscription'], ['register', 'inscription'], ['Reply', 'Répondre'], ['reply', 'réponse'], ['Replies', 'Réponses'], ['replies', 'réponses'], ['with', 'avec'], ['without', 'sans'], ['and', 'et'], ['or', 'ou'], ['for', 'pour'], ['from', 'depuis'], ['by', 'par'], ['in', 'dans'], ['to', 'à'], ['of', 'de'], ['the', 'le'], ['a ', 'un '], ['an ', 'un '],
  ],
  es: [
    ['Fleet announcements', 'Anuncios de flota'], ['fleet announcements', 'anuncios de flota'], ['Fleet calendar', 'Calendario de flota'], ['fleet calendar', 'calendario de flota'], ['Fleet management', 'Gestión de flota'], ['fleet management', 'gestión de flota'], ['Build Manager', 'Gestor de builds'], ['Build management', 'Gestión de builds'], ['New appointment', 'Nueva cita'], ['New thread', 'Nuevo hilo'], ['New guide', 'Nueva guía'], ['New build', 'Nuevo build'], ['Main navigation', 'Navegación principal'], ['Admin panel', 'Panel admin'], ['Staff panel', 'Panel del equipo'], ['Calendar operations', 'Operaciones del calendario'], ['Content moderation', 'Moderación de contenido'], ['System status', 'Estado del sistema'], ['Guide management', 'Gestión de guía'], ['Display name', 'Nombre visible'], ['Planned fleet', 'Flota planificada'], ['Application note', 'Nota de solicitud'], ['User guides', 'Guías de usuario'], ['Media embeds', 'Medios incrustados'], ['File embeds', 'Archivos incrustados'], ['Search by', 'Buscar por'], ['Loading', 'Cargando'], ['Saving', 'Guardando'], ['Posting', 'Publicando'], ['Publishing', 'Publicando'], ['Checking', 'Comprobando'], ['Waiting for', 'Esperando'], ['could not be loaded', 'no se pudo cargar'], ['could not be saved', 'no se pudo guardar'], ['could not be deleted', 'no se pudo eliminar'], ['could not be created', 'no se pudo crear'], ['could not be posted', 'no se pudo publicar'], ['could not be published', 'no se pudo publicar'], ['could not be cancelled', 'no se pudo cancelar'], ['could not be reached', 'no se pudo alcanzar'], ['failed', 'falló'], ['found', 'encontrado'], ['saved', 'guardado'], ['created', 'creado'], ['deleted', 'eliminado'], ['cancelled', 'cancelado'], ['Open', 'Abrir'], ['open', 'abrir'], ['Delete', 'Eliminar'], ['Remove', 'Quitar'], ['Cancel', 'Cancelar'], ['Close', 'Cerrar'], ['Save', 'Guardar'], ['Create', 'Crear'], ['Search', 'Buscar'], ['All', 'Todos'], ['No', 'Sin'], ['None', 'Ninguno'], ['Forum threads', 'Hilos del foro'], ['threads', 'hilos'], ['thread', 'hilo'], ['Guide', 'Guía'], ['guide', 'guía'], ['Builds', 'Builds'], ['builds', 'builds'], ['build', 'build'], ['Fleets', 'Flotas'], ['fleets', 'flotas'], ['Fleet', 'Flota'], ['fleet', 'flota'], ['Members', 'Miembros'], ['members', 'miembros'], ['Member', 'Miembro'], ['member', 'miembro'], ['Profile', 'Perfil'], ['profile', 'perfil'], ['Calendar', 'Calendario'], ['calendar', 'calendario'], ['Appointment', 'Cita'], ['appointment', 'cita'], ['Event', 'Evento'], ['event', 'evento'], ['Category', 'Categoría'], ['category', 'categoría'], ['Categories', 'Categorías'], ['categories', 'categorías'], ['Status', 'Estado'], ['status', 'estado'], ['Role', 'Rol'], ['role', 'rol'], ['Title', 'Título'], ['title', 'título'], ['Description', 'Descripción'], ['description', 'descripción'], ['Details', 'Detalles'], ['details', 'detalles'], ['Summary', 'Resumen'], ['summary', 'resumen'], ['Attachments', 'Adjuntos'], ['attachments', 'adjuntos'], ['Files', 'Archivos'], ['files', 'archivos'], ['User', 'Usuario'], ['user', 'usuario'], ['Users', 'Usuarios'], ['users', 'usuarios'], ['Moderator', 'Moderador'], ['moderator', 'moderador'], ['Password', 'Contraseña'], ['password', 'contraseña'], ['Username', 'Usuario'], ['username', 'usuario'], ['Language', 'Idioma'], ['Home', 'Inicio'], ['Back', 'Volver'], ['Empty', 'Vacío'], ['Type', 'Tipo'], ['Quantity', 'Cantidad'], ['Sailors', 'Marineros'], ['Musketeers', 'Mosqueteros'], ['Soldiers', 'Soldados'], ['Mercenaries', 'Mercenarios'], ['Ammunition', 'Munición'], ['Consumables', 'Consumibles'], ['Inventory', 'Inventario'], ['Sails', 'Velas'], ['Lantern', 'Linterna'], ['Upgrade', 'Mejora'], ['Upgrades', 'Mejoras'], ['Weapons', 'Armas'], ['Crew', 'Tripulación'], ['Ships', 'Barcos'], ['ships', 'barcos'], ['Ship', 'Barco'], ['ship', 'barco'], ['Trade', 'Comercio'], ['Trading', 'Comercio'], ['Training', 'Entrenamiento'], ['Support', 'Soporte'], ['Other', 'Otro'], ['General', 'General'], ['Economy', 'Economía'], ['Combat', 'Combate'], ['Events', 'Eventos'], ['Online', 'en línea'], ['offline', 'sin conexión'], ['active', 'activo'], ['pending', 'pendiente'], ['inactive', 'inactivo'], ['Public', 'Público'], ['public', 'público'], ['Login', 'Iniciar sesión'], ['logout', 'cerrar sesión'], ['Logout', 'Cerrar sesión'], ['Register', 'Registrarse'], ['register', 'registro'], ['Reply', 'Responder'], ['reply', 'respuesta'], ['Replies', 'Respuestas'], ['replies', 'respuestas'], ['with', 'con'], ['without', 'sin'], ['and', 'y'], ['or', 'o'], ['for', 'para'], ['from', 'desde'], ['by', 'por'], ['in', 'en'], ['to', 'a'], ['of', 'de'], ['the', 'el'], ['a ', 'un '], ['an ', 'un '],
  ],
  pt: [
    ['Fleet announcements', 'Anúncios de frota'], ['fleet announcements', 'anúncios de frota'], ['Fleet calendar', 'Calendário de frota'], ['fleet calendar', 'calendário de frota'], ['Fleet management', 'Gestão de frota'], ['fleet management', 'gestão de frota'], ['Build Manager', 'Gestor de builds'], ['Build management', 'Gestão de builds'], ['New appointment', 'Novo compromisso'], ['New thread', 'Novo tópico'], ['New guide', 'Novo guia'], ['New build', 'Novo build'], ['Main navigation', 'Navegação principal'], ['Admin panel', 'Painel admin'], ['Staff panel', 'Painel da equipa'], ['Calendar operations', 'Operações de calendário'], ['Content moderation', 'Moderação de conteúdo'], ['System status', 'Estado do sistema'], ['Guide management', 'Gestão do guia'], ['Display name', 'Nome apresentado'], ['Planned fleet', 'Frota planeada'], ['Application note', 'Nota de candidatura'], ['User guides', 'Guias de utilizador'], ['Media embeds', 'Mídia incorporada'], ['File embeds', 'Ficheiros incorporados'], ['Search by', 'Pesquisar por'], ['Loading', 'A carregar'], ['Saving', 'A guardar'], ['Posting', 'A publicar'], ['Publishing', 'A publicar'], ['Checking', 'A verificar'], ['Waiting for', 'À espera de'], ['could not be loaded', 'não pôde ser carregado'], ['could not be saved', 'não pôde ser guardado'], ['could not be deleted', 'não pôde ser eliminado'], ['could not be created', 'não pôde ser criado'], ['could not be posted', 'não pôde ser publicado'], ['could not be published', 'não pôde ser publicado'], ['could not be cancelled', 'não pôde ser cancelado'], ['could not be reached', 'não pôde ser alcançado'], ['failed', 'falhou'], ['found', 'encontrado'], ['saved', 'guardado'], ['created', 'criado'], ['deleted', 'eliminado'], ['cancelled', 'cancelado'], ['Open', 'Abrir'], ['open', 'abrir'], ['Delete', 'Eliminar'], ['Remove', 'Remover'], ['Cancel', 'Cancelar'], ['Close', 'Fechar'], ['Save', 'Guardar'], ['Create', 'Criar'], ['Search', 'Pesquisar'], ['All', 'Todos'], ['No', 'Sem'], ['None', 'Nenhum'], ['Forum threads', 'Tópicos do fórum'], ['threads', 'tópicos'], ['thread', 'tópico'], ['Guide', 'Guia'], ['guide', 'guia'], ['Builds', 'Builds'], ['builds', 'builds'], ['build', 'build'], ['Fleets', 'Frotas'], ['fleets', 'frotas'], ['Fleet', 'Frota'], ['fleet', 'frota'], ['Members', 'Membros'], ['members', 'membros'], ['Member', 'Membro'], ['member', 'membro'], ['Profile', 'Perfil'], ['profile', 'perfil'], ['Calendar', 'Calendário'], ['calendar', 'calendário'], ['Appointment', 'Compromisso'], ['appointment', 'compromisso'], ['Event', 'Evento'], ['event', 'evento'], ['Category', 'Categoria'], ['category', 'categoria'], ['Categories', 'Categorias'], ['categories', 'categorias'], ['Status', 'Estado'], ['status', 'estado'], ['Role', 'Função'], ['role', 'função'], ['Title', 'Título'], ['title', 'título'], ['Description', 'Descrição'], ['description', 'descrição'], ['Details', 'Detalhes'], ['details', 'detalhes'], ['Summary', 'Resumo'], ['summary', 'resumo'], ['Attachments', 'Anexos'], ['attachments', 'anexos'], ['Files', 'Ficheiros'], ['files', 'ficheiros'], ['User', 'Utilizador'], ['user', 'utilizador'], ['Users', 'Utilizadores'], ['users', 'utilizadores'], ['Moderator', 'Moderador'], ['moderator', 'moderador'], ['Password', 'Palavra-passe'], ['password', 'palavra-passe'], ['Username', 'Nome de utilizador'], ['username', 'nome de utilizador'], ['Language', 'Idioma'], ['Home', 'Início'], ['Back', 'Voltar'], ['Empty', 'Vazio'], ['Type', 'Tipo'], ['Quantity', 'Quantidade'], ['Sailors', 'Marinheiros'], ['Musketeers', 'Mosqueteiros'], ['Soldiers', 'Soldados'], ['Mercenaries', 'Mercenários'], ['Ammunition', 'Munição'], ['Consumables', 'Consumíveis'], ['Inventory', 'Inventário'], ['Sails', 'Velas'], ['Lantern', 'Lanterna'], ['Upgrade', 'Melhoria'], ['Upgrades', 'Melhorias'], ['Weapons', 'Armas'], ['Crew', 'Tripulação'], ['Ships', 'Navios'], ['ships', 'navios'], ['Ship', 'Navio'], ['ship', 'navio'], ['Trade', 'Comércio'], ['Trading', 'Comércio'], ['Training', 'Treino'], ['Support', 'Suporte'], ['Other', 'Outro'], ['General', 'Geral'], ['Economy', 'Economia'], ['Combat', 'Combate'], ['Events', 'Eventos'], ['Online', 'online'], ['offline', 'offline'], ['active', 'ativo'], ['pending', 'pendente'], ['inactive', 'inativo'], ['Public', 'Público'], ['public', 'público'], ['Login', 'Entrar'], ['logout', 'sair'], ['Logout', 'Sair'], ['Register', 'Registar'], ['register', 'registo'], ['Reply', 'Responder'], ['reply', 'resposta'], ['Replies', 'Respostas'], ['replies', 'respostas'], ['with', 'com'], ['without', 'sem'], ['and', 'e'], ['or', 'ou'], ['for', 'para'], ['from', 'de'], ['by', 'por'], ['in', 'em'], ['to', 'para'], ['of', 'de'], ['the', 'o'], ['a ', 'um '], ['an ', 'um '],
  ],
  ru: [
    ['Fleet announcements', 'Объявления флота'], ['fleet announcements', 'объявления флота'], ['Fleet calendar', 'Календарь флота'], ['fleet calendar', 'календарь флота'], ['Fleet management', 'Управление флотом'], ['fleet management', 'управление флотом'], ['Build Manager', 'Менеджер билдов'], ['Build management', 'Управление билдами'], ['New appointment', 'Новое событие'], ['New thread', 'Новая тема'], ['New guide', 'Новый гайд'], ['New build', 'Новый билд'], ['Main navigation', 'Главная навигация'], ['Admin panel', 'Панель администратора'], ['Staff panel', 'Панель штаба'], ['Calendar operations', 'Операции календаря'], ['Content moderation', 'Модерация контента'], ['System status', 'Статус системы'], ['Guide management', 'Управление гайдом'], ['Display name', 'Отображаемое имя'], ['Planned fleet', 'Плановый флот'], ['Application note', 'Заметка заявки'], ['User guides', 'Гайды пользователей'], ['Media embeds', 'Встроенные медиа'], ['File embeds', 'Встроенные файлы'], ['Search by', 'Поиск по'], ['Loading', 'Загрузка'], ['Saving', 'Сохранение'], ['Posting', 'Публикация'], ['Publishing', 'Публикация'], ['Checking', 'Проверка'], ['Waiting for', 'Ожидание'], ['could not be loaded', 'не удалось загрузить'], ['could not be saved', 'не удалось сохранить'], ['could not be deleted', 'не удалось удалить'], ['could not be created', 'не удалось создать'], ['could not be posted', 'не удалось опубликовать'], ['could not be published', 'не удалось опубликовать'], ['could not be cancelled', 'не удалось отменить'], ['could not be reached', 'недоступен'], ['failed', 'ошибка'], ['found', 'найдено'], ['saved', 'сохранено'], ['created', 'создано'], ['deleted', 'удалено'], ['cancelled', 'отменено'], ['Open', 'Открыть'], ['open', 'открыть'], ['Delete', 'Удалить'], ['Remove', 'Убрать'], ['Cancel', 'Отмена'], ['Close', 'Закрыть'], ['Save', 'Сохранить'], ['Create', 'Создать'], ['Search', 'Поиск'], ['All', 'Все'], ['No', 'Нет'], ['None', 'Нет'], ['Forum threads', 'Темы форума'], ['threads', 'темы'], ['thread', 'тема'], ['Guide', 'Гайд'], ['guide', 'гайд'], ['Builds', 'Билды'], ['builds', 'билды'], ['build', 'билд'], ['Fleets', 'Флоты'], ['fleets', 'флоты'], ['Fleet', 'Флот'], ['fleet', 'флот'], ['Members', 'Участники'], ['members', 'участники'], ['Member', 'Участник'], ['member', 'участник'], ['Profile', 'Профиль'], ['profile', 'профиль'], ['Calendar', 'Календарь'], ['calendar', 'календарь'], ['Appointment', 'Событие'], ['appointment', 'событие'], ['Event', 'Событие'], ['event', 'событие'], ['Category', 'Категория'], ['category', 'категория'], ['Categories', 'Категории'], ['categories', 'категории'], ['Status', 'Статус'], ['status', 'статус'], ['Role', 'Роль'], ['role', 'роль'], ['Title', 'Название'], ['title', 'название'], ['Description', 'Описание'], ['description', 'описание'], ['Details', 'Детали'], ['details', 'детали'], ['Summary', 'Сводка'], ['summary', 'сводка'], ['Attachments', 'Вложения'], ['attachments', 'вложения'], ['Files', 'Файлы'], ['files', 'файлы'], ['User', 'Пользователь'], ['user', 'пользователь'], ['Users', 'Пользователи'], ['users', 'пользователи'], ['Moderator', 'Модератор'], ['moderator', 'модератор'], ['Password', 'Пароль'], ['password', 'пароль'], ['Username', 'Логин'], ['username', 'логин'], ['Language', 'Язык'], ['Home', 'Главная'], ['Back', 'Назад'], ['Empty', 'Пусто'], ['Type', 'Тип'], ['Quantity', 'Количество'], ['Sailors', 'Матросы'], ['Musketeers', 'Мушкетеры'], ['Soldiers', 'Солдаты'], ['Mercenaries', 'Наемники'], ['Ammunition', 'Боеприпасы'], ['Consumables', 'Расходники'], ['Inventory', 'Инвентарь'], ['Sails', 'Паруса'], ['Lantern', 'Фонарь'], ['Upgrade', 'Улучшение'], ['Upgrades', 'Улучшения'], ['Weapons', 'Оружие'], ['Crew', 'Экипаж'], ['Ships', 'Корабли'], ['ships', 'корабли'], ['Ship', 'Корабль'], ['ship', 'корабль'], ['Trade', 'Торговля'], ['Trading', 'Торговля'], ['Training', 'Тренировка'], ['Support', 'Поддержка'], ['Other', 'Другое'], ['General', 'Общее'], ['Economy', 'Экономика'], ['Combat', 'Бой'], ['Events', 'События'], ['Online', 'онлайн'], ['offline', 'офлайн'], ['active', 'активно'], ['pending', 'ожидает'], ['inactive', 'неактивно'], ['Public', 'Публичный'], ['public', 'публичный'], ['Login', 'Войти'], ['logout', 'выйти'], ['Logout', 'Выйти'], ['Register', 'Регистрация'], ['register', 'регистрация'], ['Reply', 'Ответить'], ['reply', 'ответ'], ['Replies', 'Ответы'], ['replies', 'ответы'], ['with', 'с'], ['without', 'без'], ['and', 'и'], ['or', 'или'], ['for', 'для'], ['from', 'из'], ['by', 'от'], ['in', 'в'], ['to', 'к'], ['of', ''], ['the', ''], ['a ', ''], ['an ', ''],
  ],
  cn: [
    ['Fleet announcements', '舰队公告'], ['fleet announcements', '舰队公告'], ['Fleet calendar', '舰队日历'], ['fleet calendar', '舰队日历'], ['Fleet management', '舰队管理'], ['fleet management', '舰队管理'], ['Build Manager', '配装管理器'], ['Build management', '配装管理'], ['New appointment', '新日程'], ['New thread', '新主题'], ['New guide', '新指南'], ['New build', '新配装'], ['Main navigation', '主导航'], ['Admin panel', '管理员面板'], ['Staff panel', '管理面板'], ['Calendar operations', '日历操作'], ['Content moderation', '内容审核'], ['System status', '系统状态'], ['Guide management', '指南管理'], ['Display name', '显示名称'], ['Planned fleet', '计划舰队'], ['Application note', '申请备注'], ['User guides', '用户指南'], ['Media embeds', '媒体嵌入'], ['File embeds', '文件嵌入'], ['Search by', '搜索'], ['Loading', '正在加载'], ['Saving', '正在保存'], ['Posting', '正在发布'], ['Publishing', '正在发布'], ['Checking', '正在检查'], ['Waiting for', '正在等待'], ['could not be loaded', '无法加载'], ['could not be saved', '无法保存'], ['could not be deleted', '无法删除'], ['could not be created', '无法创建'], ['could not be posted', '无法发布'], ['could not be published', '无法发布'], ['could not be cancelled', '无法取消'], ['could not be reached', '无法访问'], ['failed', '失败'], ['found', '已找到'], ['saved', '已保存'], ['created', '已创建'], ['deleted', '已删除'], ['cancelled', '已取消'], ['Open', '打开'], ['open', '打开'], ['Delete', '删除'], ['Remove', '移除'], ['Cancel', '取消'], ['Close', '关闭'], ['Save', '保存'], ['Create', '创建'], ['Search', '搜索'], ['All', '全部'], ['No', '无'], ['None', '无'], ['Forum threads', '论坛主题'], ['threads', '主题'], ['thread', '主题'], ['Guide', '指南'], ['guide', '指南'], ['Guides', '指南'], ['Builds', '配装'], ['builds', '配装'], ['build', '配装'], ['Fleets', '舰队'], ['fleets', '舰队'], ['Fleet', '舰队'], ['fleet', '舰队'], ['Members', '成员'], ['members', '成员'], ['Member', '成员'], ['member', '成员'], ['Profile', '个人资料'], ['profile', '个人资料'], ['Calendar', '日历'], ['calendar', '日历'], ['Appointment', '日程'], ['appointment', '日程'], ['Event', '事件'], ['event', '事件'], ['Category', '分类'], ['category', '分类'], ['Categories', '分类'], ['categories', '分类'], ['Status', '状态'], ['status', '状态'], ['Role', '角色'], ['role', '角色'], ['Title', '标题'], ['title', '标题'], ['Description', '描述'], ['description', '描述'], ['Details', '详情'], ['details', '详情'], ['Summary', '摘要'], ['summary', '摘要'], ['Attachments', '附件'], ['attachments', '附件'], ['Files', '文件'], ['files', '文件'], ['User', '用户'], ['user', '用户'], ['Users', '用户'], ['users', '用户'], ['Moderator', '版主'], ['moderator', '版主'], ['Password', '密码'], ['password', '密码'], ['Username', '用户名'], ['username', '用户名'], ['Language', '语言'], ['Home', '首页'], ['Back', '返回'], ['Empty', '空'], ['Type', '类型'], ['Quantity', '数量'], ['Sailors', '水手'], ['Musketeers', '火枪手'], ['Soldiers', '士兵'], ['Mercenaries', '雇佣兵'], ['Ammunition', '弹药'], ['Consumables', '消耗品'], ['Inventory', '库存'], ['Sails', '帆'], ['Lantern', '灯笼'], ['Upgrade', '升级'], ['Upgrades', '升级'], ['Weapons', '武器'], ['Crew', '船员'], ['Ships', '船只'], ['ships', '船只'], ['Ship', '船只'], ['ship', '船只'], ['Trade', '贸易'], ['Trading', '贸易'], ['Training', '训练'], ['Support', '支援'], ['Other', '其他'], ['General', '通用'], ['Economy', '经济'], ['Combat', '战斗'], ['Events', '活动'], ['Online', '在线'], ['offline', '离线'], ['active', '活跃'], ['pending', '待处理'], ['inactive', '停用'], ['Public', '公开'], ['public', '公开'], ['Login', '登录'], ['logout', '退出'], ['Logout', '退出'], ['Register', '注册'], ['register', '注册'], ['Reply', '回复'], ['reply', '回复'], ['Replies', '回复'], ['replies', '回复'], ['with', '包含'], ['without', '不含'], ['and', '和'], ['or', '或'], ['for', '用于'], ['from', '来自'], ['by', '由'], ['in', '在'], ['to', '到'], ['of', '的'], ['the', ''], ['a ', ''], ['an ', ''],
  ],
}

function isPlainObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value)
}

function protectPlaceholders(value) {
  const placeholders = []
  const text = String(value).replace(/\{[^}]+\}/g, (match) => {
    const token = `${TEXT_PLACEHOLDER}${placeholders.length}__`
    placeholders.push(match)
    return token
  })
  return { text, placeholders }
}

function restorePlaceholders(value, placeholders) {
  return placeholders.reduce((output, placeholder, index) => output.replace(`${TEXT_PLACEHOLDER}${index}__`, placeholder), value)
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function applyTerms(value, locale) {
  const replacements = termTranslations[locale] || []
  let output = value
  for (const [source, target] of [...replacements].sort((a, b) => b[0].length - a[0].length)) {
    output = output.replace(new RegExp(escapeRegExp(source), 'g'), target)
  }
  return output
}

function localizeString(locale, value) {
  if (typeof value !== 'string') return value
  if (!value.trim()) return value
  if (neutralValues.has(value)) return value

  const exact = exactTranslations[locale]?.[value] ?? generatedPhraseTranslations[locale]?.[value]
  if (exact) return exact

  const { text, placeholders } = protectPlaceholders(value)
  let translated = applyTerms(text, locale).replace(/\s+/g, ' ').trim()
  translated = restorePlaceholders(translated, placeholders)

  if (translated === value && localePrefixes[locale]) {
    return `${localePrefixes[locale]} · ${value}`
  }

  return translated
}

function fillNode(target, englishNode, locale) {
  if (!isPlainObject(englishNode)) return

  for (const [key, englishValue] of Object.entries(englishNode)) {
    if (isPlainObject(englishValue)) {
      if (!isPlainObject(target[key])) target[key] = {}
      fillNode(target[key], englishValue, locale)
      continue
    }

    if (target[key] === undefined || target[key] === englishValue) {
      target[key] = localizeString(locale, englishValue)
    }
  }
}

export function fillLocalizedMessages(messages, defaultLocale = 'en') {
  const englishMessages = messages[defaultLocale]
  for (const locale of Object.keys(messages)) {
    if (locale === defaultLocale) continue
    fillNode(messages[locale], englishMessages, locale)
  }
}

export function flattenMessages(obj, prefix = '') {
  return Object.entries(obj || {}).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key
    return isPlainObject(value) ? flattenMessages(value, path) : [[path, value]]
  })
}

export function isLocaleNeutralValue(value) {
  return neutralValues.has(value)
}
