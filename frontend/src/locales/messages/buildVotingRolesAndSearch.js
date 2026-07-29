export const buildVotingRolesAndSearchMessages = {
  en: {
    builds: {
      voting: { upvotes: 'Upvotes', upvote: 'Upvote', remove: 'Remove vote', error: 'Your vote could not be saved.' },
      create: { specialCrew: { searchPlaceholder: 'Search specialists…', noMatches: 'No matching specialists.' } },
    },
    admin: { buildRoles: {
      title: 'Build roles', subtitle: 'Create and maintain the role catalog and assign roles to builds.',
      slug: 'Key', label: 'Name', description: 'Description', sortOrder: 'Order', create: 'Create role',
      save: 'Save', delete: 'Delete', confirmDelete: 'Delete this role?', deleteNow: 'Delete now', assign: 'Build role', created: 'Build role created.', saved: 'Build role saved.',
      deleted: 'Build role deleted.', createError: 'The build role could not be created.', saveError: 'The build role could not be saved.',
      deleteError: 'The build role could not be deleted.', assignError: 'The build role could not be assigned.',
    } },
  },
  de: {
    builds: {
      voting: { upvotes: 'Stimmen', upvote: 'Stimme abgeben', remove: 'Stimme entfernen', error: 'Deine Stimme konnte nicht gespeichert werden.' },
      create: { specialCrew: { searchPlaceholder: 'Specialists durchsuchen…', noMatches: 'Keine passenden Specialists.' } },
    },
    admin: { buildRoles: {
      title: 'Build-Rollen', subtitle: 'Rollenkatalog verwalten und Rollen direkt Builds zuweisen.',
      slug: 'Schlüssel', label: 'Bezeichnung', description: 'Beschreibung', sortOrder: 'Reihenfolge', create: 'Rolle anlegen',
      save: 'Speichern', delete: 'Löschen', confirmDelete: 'Diese Rolle löschen?', deleteNow: 'Jetzt löschen', assign: 'Build-Rolle', created: 'Build-Rolle angelegt.', saved: 'Build-Rolle gespeichert.',
      deleted: 'Build-Rolle gelöscht.', createError: 'Die Build-Rolle konnte nicht angelegt werden.', saveError: 'Die Build-Rolle konnte nicht gespeichert werden.',
      deleteError: 'Die Build-Rolle konnte nicht gelöscht werden.', assignError: 'Die Build-Rolle konnte nicht zugewiesen werden.',
    } },
  },
  fr: {
    builds: { voting: { upvotes: 'Votes', upvote: 'Voter', remove: 'Retirer le vote', error: 'Votre vote n’a pas pu être enregistré.' }, create: { specialCrew: { searchPlaceholder: 'Rechercher des spécialistes…', noMatches: 'Aucun spécialiste correspondant.' } } },
    admin: { buildRoles: { title: 'Rôles de build', subtitle: 'Gérez le catalogue et attribuez les rôles aux builds.', slug: 'Clé', label: 'Nom', description: 'Description', sortOrder: 'Ordre', create: 'Créer', save: 'Enregistrer', delete: 'Supprimer', confirmDelete: 'Supprimer ce rôle ?', deleteNow: 'Supprimer', assign: 'Rôle du build', created: 'Rôle créé.', saved: 'Rôle enregistré.', deleted: 'Rôle supprimé.', createError: 'Impossible de créer le rôle.', saveError: 'Impossible d’enregistrer le rôle.', deleteError: 'Impossible de supprimer le rôle.', assignError: 'Impossible d’attribuer le rôle.' } },
  },
  es: {
    builds: { voting: { upvotes: 'Votos', upvote: 'Votar', remove: 'Quitar voto', error: 'No se pudo guardar tu voto.' }, create: { specialCrew: { searchPlaceholder: 'Buscar especialistas…', noMatches: 'No hay especialistas coincidentes.' } } },
    admin: { buildRoles: { title: 'Roles de build', subtitle: 'Gestiona el catálogo y asigna roles a los builds.', slug: 'Clave', label: 'Nombre', description: 'Descripción', sortOrder: 'Orden', create: 'Crear rol', save: 'Guardar', delete: 'Eliminar', confirmDelete: '¿Eliminar este rol?', deleteNow: 'Eliminar ahora', assign: 'Rol del build', created: 'Rol creado.', saved: 'Rol guardado.', deleted: 'Rol eliminado.', createError: 'No se pudo crear el rol.', saveError: 'No se pudo guardar el rol.', deleteError: 'No se pudo eliminar el rol.', assignError: 'No se pudo asignar el rol.' } },
  },
  pt: {
    builds: { voting: { upvotes: 'Votos', upvote: 'Votar', remove: 'Remover voto', error: 'Não foi possível guardar o voto.' }, create: { specialCrew: { searchPlaceholder: 'Pesquisar especialistas…', noMatches: 'Nenhum especialista correspondente.' } } },
    admin: { buildRoles: { title: 'Funções de build', subtitle: 'Gerir o catálogo e atribuir funções aos builds.', slug: 'Chave', label: 'Nome', description: 'Descrição', sortOrder: 'Ordem', create: 'Criar função', save: 'Guardar', delete: 'Eliminar', confirmDelete: 'Eliminar esta função?', deleteNow: 'Eliminar agora', assign: 'Função do build', created: 'Função criada.', saved: 'Função guardada.', deleted: 'Função eliminada.', createError: 'Não foi possível criar a função.', saveError: 'Não foi possível guardar a função.', deleteError: 'Não foi possível eliminar a função.', assignError: 'Não foi possível atribuir a função.' } },
  },
  ru: {
    builds: { voting: { upvotes: 'Голоса', upvote: 'Поддержать', remove: 'Убрать голос', error: 'Не удалось сохранить голос.' }, create: { specialCrew: { searchPlaceholder: 'Поиск специалистов…', noMatches: 'Подходящие специалисты не найдены.' } } },
    admin: { buildRoles: { title: 'Роли билдов', subtitle: 'Управляйте каталогом и назначайте роли билдам.', slug: 'Ключ', label: 'Название', description: 'Описание', sortOrder: 'Порядок', create: 'Создать роль', save: 'Сохранить', delete: 'Удалить', confirmDelete: 'Удалить эту роль?', deleteNow: 'Удалить', assign: 'Роль билда', created: 'Роль создана.', saved: 'Роль сохранена.', deleted: 'Роль удалена.', createError: 'Не удалось создать роль.', saveError: 'Не удалось сохранить роль.', deleteError: 'Не удалось удалить роль.', assignError: 'Не удалось назначить роль.' } },
  },
  cn: {
    builds: { voting: { upvotes: '赞成票', upvote: '赞成', remove: '取消投票', error: '无法保存你的投票。' }, create: { specialCrew: { searchPlaceholder: '搜索专家…', noMatches: '没有匹配的专家。' } } },
    admin: { buildRoles: { title: 'Build 角色', subtitle: '管理角色目录并为 Build 分配角色。', slug: '键', label: '名称', description: '说明', sortOrder: '顺序', create: '创建角色', save: '保存', delete: '删除', confirmDelete: '删除此角色？', deleteNow: '立即删除', assign: 'Build 角色', created: '角色已创建。', saved: '角色已保存。', deleted: '角色已删除。', createError: '无法创建角色。', saveError: '无法保存角色。', deleteError: '无法删除角色。', assignError: '无法分配角色。' } },
  },
}
