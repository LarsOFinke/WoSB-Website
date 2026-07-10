export const calendarRoutes = [
  {
    path: '/calendar',
    name: 'calendar',
    component: () => import('./pages/CalendarPage.vue'),
    meta: { requiresUser: true, titleKey: 'common.calendar' },
  },
  {
    path: '/calendar/new',
    name: 'calendar-new',
    component: () => import('./pages/CalendarCreatePage.vue'),
    meta: { requiresStaff: true, titleKey: 'common.calendar' },
  },
]
