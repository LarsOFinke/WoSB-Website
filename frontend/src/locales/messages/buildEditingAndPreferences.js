export const buildEditingAndPreferencesMessages = {
  en: {
    builds: {
      create: { crew: { sailorMinimum: 'Required sailor minimum: {value}', workingSpeed: 'Working speed: {value}%', tooFewSailors: 'Only {current} of {minimum} required sailors are assigned.' }, saveReadiness: { blockedTitle: 'This build cannot be saved yet', blockedHint: 'Resolve the following requirements. The list updates immediately as you edit.', readyTitle: 'Build is ready to save', readyHint: 'All required values and capacity checks are valid.', reasons: { name: 'Enter a build name.', ship: 'Select a ship.', sailors: 'Assign at least {minimum} sailors (currently {current}).', crew: 'Crew allocation {current} exceeds the effective capacity of {maximum}.', upgrade5: 'Upgrade slot 5 is not unlocked.', upgrade6: 'Upgrade slot 6 requires Structural Expansion or two one-slot sources.', upgrade7: 'Upgrade slot 7 requires Structural Expansion plus the upgrade add-on slot or a ship-specific extra slot.', upgrade8: 'Upgrade slot 8 requires Structural Expansion, the upgrade add-on slot, and a ship-specific extra slot.', weapons: 'One or more weapon positions are incompatible or over capacity.', specialists: 'Select no more than {maximum} distinct specialists.' } } },
      statLabels: { sailor_minimum: 'Required sailor minimum' },
      share: { action: 'Share Build', copied: 'Build link copied.', error: 'The build link could not be copied.' },
      edit: {
        action: 'Edit build',
        title: 'Edit build',
        subtitle: 'Update the ship, equipment, crew and inventory with the same live validation used during creation.',
        loadError: 'The build could not be loaded for editing.',
        notAllowed: 'You can only edit your own non-template builds.',
        save: 'Save changes',
        saving: 'Saving changes ...',
        saveError: 'The build changes could not be saved.',
      },
    },
    profile: {
      completion: {
        label: 'Profile completion',
        hint: 'Add preferences to make your profile more useful for fleet planning.',
        complete: 'Your profile is ready for fleet planning.',
      },
      preferenceTransfer: {
        available: 'Available',
        selected: 'Selected',
        select: 'Select',
        remove: 'Remove',
        noneAvailable: 'All entries are selected.',
        noneSelected: 'No entries selected yet.',
      },
    },
  },
  de: {
    builds: {
      create: { crew: { sailorMinimum: 'Erforderliche Mindestmatrosen: {value}', workingSpeed: 'Arbeitsgeschwindigkeit: {value} %', tooFewSailors: 'Nur {current} von {minimum} erforderlichen Matrosen sind zugewiesen.' }, saveReadiness: { blockedTitle: 'Dieser Build kann noch nicht gespeichert werden', blockedHint: 'Behebe die folgenden Punkte. Die Liste aktualisiert sich direkt bei Änderungen.', readyTitle: 'Build ist speicherbereit', readyHint: 'Alle Pflichtangaben und Kapazitätsprüfungen sind gültig.', reasons: { name: 'Einen Build-Namen eingeben.', ship: 'Ein Schiff auswählen.', sailors: 'Mindestens {minimum} Matrosen zuweisen (aktuell {current}).', crew: 'Die Besatzung {current} überschreitet die effektive Kapazität von {maximum}.', upgrade5: 'Upgrade-Platz 5 ist nicht freigeschaltet.', upgrade6: 'Upgrade-Platz 6 benötigt Structural Expansion oder zwei einzelne Slot-Quellen.', upgrade7: 'Upgrade-Platz 7 benötigt Structural Expansion plus Upgrade-Add-on-Slot oder einen schiffsspezifischen Extra-Slot.', upgrade8: 'Upgrade-Platz 8 benötigt Structural Expansion, Upgrade-Add-on-Slot und einen schiffsspezifischen Extra-Slot.', weapons: 'Mindestens eine Waffenposition ist inkompatibel oder überbelegt.', specialists: 'Höchstens {maximum} unterschiedliche Specialists auswählen.' } } },
      statLabels: { sailor_minimum: 'Erforderliche Mindestmatrosen' },
      share: { action: 'Build teilen', copied: 'Build-Link kopiert.', error: 'Der Build-Link konnte nicht kopiert werden.' },
      edit: {
        action: 'Build bearbeiten',
        title: 'Build bearbeiten',
        subtitle: 'Schiff, Ausrüstung, Besatzung und Inventar mit derselben Live-Validierung wie beim Erstellen anpassen.',
        loadError: 'Der Build konnte nicht zum Bearbeiten geladen werden.',
        notAllowed: 'Du kannst nur eigene Builds bearbeiten, die keine offiziellen Vorlagen sind.',
        save: 'Änderungen speichern',
        saving: 'Änderungen werden gespeichert ...',
        saveError: 'Die Build-Änderungen konnten nicht gespeichert werden.',
      },
    },
    profile: {
      completion: {
        label: 'Profil vollständig',
        hint: 'Ergänze Präferenzen, damit dein Profil für die Flottenplanung aussagekräftiger wird.',
        complete: 'Dein Profil ist für die Flottenplanung vollständig.',
      },
      preferenceTransfer: {
        available: 'Verfügbar',
        selected: 'Ausgewählt',
        select: 'Auswählen',
        remove: 'Entfernen',
        noneAvailable: 'Alle Einträge sind ausgewählt.',
        noneSelected: 'Noch keine Einträge ausgewählt.',
      },
    },
  },
  fr: {
    builds: {
      create: { crew: { sailorMinimum: 'Minimum de marins requis : {value}', workingSpeed: 'Vitesse de travail : {value} %', tooFewSailors: 'Seulement {current} marins sur les {minimum} requis sont affectés.' }, saveReadiness: { blockedTitle: 'Ce build ne peut pas encore être enregistré', blockedHint: 'Corrigez les points suivants. La liste se met à jour immédiatement.', readyTitle: 'Le build est prêt', readyHint: 'Toutes les exigences sont valides.', reasons: { name: 'Saisissez un nom.', ship: 'Sélectionnez un navire.', sailors: 'Affectez au moins {minimum} marins (actuellement {current}).', crew: 'L’équipage {current} dépasse la capacité de {maximum}.', upgrade5: 'L’emplacement 5 est verrouillé.', upgrade6: 'L’emplacement 6 exige Structural Expansion ou deux sources d’un emplacement.', upgrade7: 'L’emplacement 7 exige Structural Expansion plus l’emplacement d’amélioration additionnel ou un emplacement supplémentaire du navire.', upgrade8: 'L’emplacement 8 exige Structural Expansion, l’emplacement d’amélioration additionnel et un emplacement supplémentaire du navire.', weapons: 'Une arme est incompatible ou dépasse la capacité.', specialists: 'Sélectionnez au maximum {maximum} spécialistes distincts.' } } },
      statLabels: { sailor_minimum: 'Minimum de marins requis' },
      share: { action: 'Partager le build', copied: 'Lien du build copié.', error: 'Impossible de copier le lien.' },
      edit: {
        action: 'Modifier le build', title: 'Modifier le build',
        subtitle: 'Modifiez le navire, l’équipement, l’équipage et l’inventaire avec la même validation en direct que lors de la création.',
        loadError: 'Le build n’a pas pu être chargé pour modification.', notAllowed: 'Vous ne pouvez modifier que vos propres builds hors modèles officiels.',
        save: 'Enregistrer les modifications', saving: 'Enregistrement ...', saveError: 'Les modifications du build n’ont pas pu être enregistrées.',
      },
    },
    profile: { completion: { label: 'Profil complété', hint: 'Ajoutez vos préférences pour faciliter la planification de la flotte.', complete: 'Votre profil est prêt pour la planification de la flotte.' }, preferenceTransfer: { available: 'Disponibles', selected: 'Sélectionnés', select: 'Sélectionner', remove: 'Retirer', noneAvailable: 'Toutes les entrées sont sélectionnées.', noneSelected: 'Aucune entrée sélectionnée.' } },
  },
  es: {
    builds: {
      create: { crew: { sailorMinimum: 'Mínimo de marineros requerido: {value}', workingSpeed: 'Velocidad de trabajo: {value} %', tooFewSailors: 'Solo hay {current} de {minimum} marineros requeridos.' }, saveReadiness: { blockedTitle: 'Este build aún no se puede guardar', blockedHint: 'Resuelve los siguientes requisitos.', readyTitle: 'El build está listo', readyHint: 'Todos los requisitos son válidos.', reasons: { name: 'Introduce un nombre.', ship: 'Selecciona un barco.', sailors: 'Asigna al menos {minimum} marineros (actualmente {current}).', crew: 'La tripulación {current} supera la capacidad {maximum}.', upgrade5: 'La ranura 5 está bloqueada.', upgrade6: 'La ranura 6 requiere Structural Expansion o dos fuentes de un espacio.', upgrade7: 'La ranura 7 requiere Structural Expansion más el espacio adicional de mejora o un espacio adicional del barco.', upgrade8: 'La ranura 8 requiere Structural Expansion, el espacio adicional de mejora y un espacio adicional del barco.', weapons: 'Alguna arma es incompatible o supera la capacidad.', specialists: 'Selecciona como máximo {maximum} especialistas distintos.' } } },
      statLabels: { sailor_minimum: 'Mínimo de marineros requerido' },
      share: { action: 'Compartir build', copied: 'Enlace copiado.', error: 'No se pudo copiar el enlace.' },
      edit: {
        action: 'Editar build', title: 'Editar build',
        subtitle: 'Actualiza el barco, el equipo, la tripulación y el inventario con la misma validación en vivo usada al crear.',
        loadError: 'No se pudo cargar el build para editarlo.', notAllowed: 'Solo puedes editar tus propios builds que no sean plantillas oficiales.',
        save: 'Guardar cambios', saving: 'Guardando cambios ...', saveError: 'No se pudieron guardar los cambios del build.',
      },
    },
    profile: { completion: { label: 'Perfil completado', hint: 'Añade preferencias para facilitar la planificación de la flota.', complete: 'Tu perfil está listo para la planificación de la flota.' }, preferenceTransfer: { available: 'Disponibles', selected: 'Seleccionados', select: 'Seleccionar', remove: 'Quitar', noneAvailable: 'Todas las entradas están seleccionadas.', noneSelected: 'Todavía no hay entradas seleccionadas.' } },
  },
  pt: {
    builds: {
      create: { crew: { sailorMinimum: 'Mínimo de marinheiros exigido: {value}', workingSpeed: 'Velocidade de trabalho: {value}%', tooFewSailors: 'Só foram atribuídos {current} de {minimum} marinheiros.' }, saveReadiness: { blockedTitle: 'Este build ainda não pode ser guardado', blockedHint: 'Resolva os requisitos seguintes.', readyTitle: 'O build está pronto', readyHint: 'Todos os requisitos são válidos.', reasons: { name: 'Introduza um nome.', ship: 'Selecione um navio.', sailors: 'Atribua pelo menos {minimum} marinheiros (atualmente {current}).', crew: 'A tripulação {current} excede a capacidade {maximum}.', upgrade5: 'O espaço 5 está bloqueado.', upgrade6: 'O espaço 6 requer Structural Expansion ou duas fontes de um espaço.', upgrade7: 'O espaço 7 requer Structural Expansion mais o espaço adicional de melhoria ou um espaço extra do navio.', upgrade8: 'O espaço 8 requer Structural Expansion, o espaço adicional de melhoria e um espaço extra do navio.', weapons: 'Uma arma é incompatível ou excede a capacidade.', specialists: 'Selecione no máximo {maximum} especialistas distintos.' } } },
      statLabels: { sailor_minimum: 'Mínimo de marinheiros exigido' },
      share: { action: 'Partilhar build', copied: 'Ligação copiada.', error: 'Não foi possível copiar a ligação.' },
      edit: {
        action: 'Editar build', title: 'Editar build',
        subtitle: 'Atualize o navio, equipamento, tripulação e inventário com a mesma validação em tempo real da criação.',
        loadError: 'Não foi possível carregar o build para edição.', notAllowed: 'Só pode editar os seus próprios builds que não sejam modelos oficiais.',
        save: 'Guardar alterações', saving: 'A guardar alterações ...', saveError: 'Não foi possível guardar as alterações do build.',
      },
    },
    profile: { completion: { label: 'Perfil completo', hint: 'Adicione preferências para facilitar o planeamento da frota.', complete: 'O seu perfil está pronto para o planeamento da frota.' }, preferenceTransfer: { available: 'Disponíveis', selected: 'Selecionados', select: 'Selecionar', remove: 'Remover', noneAvailable: 'Todas as entradas estão selecionadas.', noneSelected: 'Ainda não há entradas selecionadas.' } },
  },
  ru: {
    builds: {
      create: { crew: { sailorMinimum: 'Требуемый минимум матросов: {value}', workingSpeed: 'Рабочая скорость: {value}%', tooFewSailors: 'Назначено {current} из {minimum} требуемых матросов.' }, saveReadiness: { blockedTitle: 'Билд пока нельзя сохранить', blockedHint: 'Исправьте следующие требования.', readyTitle: 'Билд готов к сохранению', readyHint: 'Все требования выполнены.', reasons: { name: 'Введите название.', ship: 'Выберите корабль.', sailors: 'Назначьте не менее {minimum} матросов (сейчас {current}).', crew: 'Экипаж {current} превышает вместимость {maximum}.', upgrade5: 'Слот 5 заблокирован.', upgrade6: 'Для слота 6 нужна Structural Expansion или два источника по одному слоту.', upgrade7: 'Для слота 7 нужна Structural Expansion и дополнительный слот улучшения либо дополнительный слот корабля.', upgrade8: 'Для слота 8 нужны Structural Expansion, дополнительный слот улучшения и дополнительный слот корабля.', weapons: 'Оружие несовместимо или превышает вместимость.', specialists: 'Выберите не более {maximum} разных специалистов.' } } },
      statLabels: { sailor_minimum: 'Требуемый минимум матросов' },
      share: { action: 'Поделиться билдом', copied: 'Ссылка скопирована.', error: 'Не удалось скопировать ссылку.' },
      edit: {
        action: 'Изменить билд', title: 'Изменить билд',
        subtitle: 'Измените корабль, оснащение, экипаж и инвентарь с той же проверкой, что и при создании.',
        loadError: 'Не удалось загрузить билд для редактирования.', notAllowed: 'Можно редактировать только свои билды, не являющиеся официальными шаблонами.',
        save: 'Сохранить изменения', saving: 'Сохранение ...', saveError: 'Не удалось сохранить изменения билда.',
      },
    },
    profile: { completion: { label: 'Заполнение профиля', hint: 'Добавьте предпочтения, чтобы упростить планирование флота.', complete: 'Профиль готов для планирования флота.' }, preferenceTransfer: { available: 'Доступно', selected: 'Выбрано', select: 'Выбрать', remove: 'Убрать', noneAvailable: 'Все записи выбраны.', noneSelected: 'Пока ничего не выбрано.' } },
  },
  cn: {
    builds: {
      create: { crew: { sailorMinimum: '所需最低水手数：{value}', workingSpeed: '工作速度：{value}%', tooFewSailors: '当前分配 {current} 名水手，最低需要 {minimum} 名。' }, saveReadiness: { blockedTitle: '此配装暂时无法保存', blockedHint: '请解决以下要求，列表会随编辑即时更新。', readyTitle: '配装可以保存', readyHint: '所有必填项和容量检查均已通过。', reasons: { name: '请输入配装名称。', ship: '请选择舰船。', sailors: '至少分配 {minimum} 名水手（当前 {current}）。', crew: '船员 {current} 超过有效容量 {maximum}。', upgrade5: '升级槽位 5 尚未解锁。', upgrade6: '升级槽位 6 需要 Structural Expansion，或两个单槽位来源。', upgrade7: '升级槽位 7 需要 Structural Expansion，加上额外升级槽或舰船专属额外槽位。', upgrade8: '升级槽位 8 需要 Structural Expansion、额外升级槽和舰船专属额外槽位。', weapons: '存在不兼容或超出容量的武器位置。', specialists: '最多选择 {maximum} 种不同专家。' } } },
      statLabels: { sailor_minimum: '所需最低水手数' },
      share: { action: '分享配装', copied: '配装链接已复制。', error: '无法复制配装链接。' },
      edit: {
        action: '编辑配装', title: '编辑配装',
        subtitle: '使用与创建时相同的实时校验更新舰船、装备、船员和库存。',
        loadError: '无法加载配装进行编辑。', notAllowed: '只能编辑你自己的非官方模板配装。',
        save: '保存更改', saving: '正在保存更改…', saveError: '无法保存配装更改。',
      },
    },
    profile: { completion: { label: '资料完整度', hint: '添加偏好，让舰队规划更准确。', complete: '你的资料已可用于舰队规划。' }, preferenceTransfer: { available: '可选', selected: '已选', select: '选择', remove: '移除', noneAvailable: '所有条目均已选择。', noneSelected: '尚未选择任何条目。' } },
  },
}
