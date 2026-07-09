import { cloneMessages, mergeMessages } from '../utils'
import { adminDashboardMessages } from './adminDashboard'
import { appShellMessages } from './appShell'
import { authAdminProfileMessages } from './authAdminProfile'
import { baseMessages } from './base'
import { contentModulesAndBuildStatsMessages } from './contentModulesAndBuildStats'
import { fleetCalendarMessages } from './fleetCalendar'
import { fleetManagementMessages } from './fleetManagement'
import { finalNavigationAndGroupSignupMessages } from './finalNavigationAndGroupSignup'
import { localeCompletenessMessages } from './localeCompleteness'
import { staffPanelMessages } from './staffPanel'
import { fillLocalizedMessages } from '../autoLocalization'
import { groupManagementMessages } from './groupManagement'
import { ironCrownFleetHubMessages } from './ironCrownFleetHub'
import { userBuildsAndPasswordMessages } from './userBuildsAndPassword'

const messageLayers = [
  appShellMessages,
  authAdminProfileMessages,
  userBuildsAndPasswordMessages,
  groupManagementMessages,
  ironCrownFleetHubMessages,
  contentModulesAndBuildStatsMessages,
  fleetCalendarMessages,
  fleetManagementMessages,
  staffPanelMessages,
  adminDashboardMessages,
  finalNavigationAndGroupSignupMessages,
]

export const messages = cloneMessages(baseMessages)

for (const localeCode of Object.keys(messages)) {
  if (localeCode !== 'en') {
    mergeMessages(messages[localeCode], baseMessages.en)
  }
  for (const layer of messageLayers) {
    mergeMessages(messages[localeCode], layer.en)
    mergeMessages(messages[localeCode], layer[localeCode])
  }
}

fillLocalizedMessages(messages)

for (const localeCode of Object.keys(messages)) {
  mergeMessages(messages[localeCode], localeCompletenessMessages[localeCode])
}
