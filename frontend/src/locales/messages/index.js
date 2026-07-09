import { cloneMessages, mergeMessages } from '../utils'
import { authAdminProfileMessages } from './authAdminProfile'
import { baseMessages } from './base'
import { contentModulesAndBuildStatsMessages } from './contentModulesAndBuildStats'
import { fleetCalendarMessages } from './fleetCalendar'
import { fleetManagementMessages } from './fleetManagement'
import { staffPanelMessages } from './staffPanel'
import { groupManagementMessages } from './groupManagement'
import { ironCrownFleetHubMessages } from './ironCrownFleetHub'
import { userBuildsAndPasswordMessages } from './userBuildsAndPassword'

const messageLayers = [
  authAdminProfileMessages,
  userBuildsAndPasswordMessages,
  groupManagementMessages,
  ironCrownFleetHubMessages,
  contentModulesAndBuildStatsMessages,
  fleetCalendarMessages,
  fleetManagementMessages,
  staffPanelMessages,
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
