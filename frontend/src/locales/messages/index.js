import { cloneMessages, mergeMessages } from '../utils'
import { authAdminProfileMessages } from './authAdminProfile'
import { baseMessages } from './base'
import { contentModulesAndBuildStatsMessages } from './contentModulesAndBuildStats'
import { fleetCalendarMessages } from './fleetCalendar'
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
]

export const messages = cloneMessages(baseMessages)

for (const localeCode of Object.keys(messages)) {
  for (const layer of messageLayers) {
    mergeMessages(messages[localeCode], layer.en)
    mergeMessages(messages[localeCode], layer[localeCode])
  }
}
