import { cloneMessages, mergeMessages } from '../utils'
import { adminDashboardMessages } from './adminDashboard'
import { appShellMessages } from './appShell'
import { authAdminProfileMessages } from './authAdminProfile'
import { baseMessages } from './base'
import { buildDesignerEquipmentRulesMessages } from './buildDesignerEquipmentRules'
import { buildEditingAndPreferencesMessages } from './buildEditingAndPreferences'
import { contentModulesAndBuildStatsMessages } from './contentModulesAndBuildStats'
import { dateFieldFixMessages } from './dateFieldFixes'
import { fleetCalendarMessages } from './fleetCalendar'
import { fleetIdentityMessages } from './fleetIdentity'
import { fleetManagementMessages } from './fleetManagement'
import { finalNavigationAndGroupSignupMessages } from './finalNavigationAndGroupSignup'
import { localeCompletenessMessages } from './localeCompleteness'
import { newcomerGuideMessages } from './newcomerGuide'
import { mySquadsWorkspaceMessages } from './mySquadsWorkspace'
import { privacyMessages } from './privacy'
import { masterDataMessages } from './masterData'
import { staffPanelMessages } from './staffPanel'
import { staffWorkspaceOverhaulMessages } from './staffWorkspaceOverhaul'
import { systemOperationsMessages } from './systemOperations'
import { securityAuditDashboardMessages } from './securityAuditDashboard'
import { ipBlockManagementMessages } from './ipBlockManagement'
import { outboundWebhookManagementMessages } from './outboundWebhookManagement'
import { discordWebhooksMessages } from './discordWebhooks'
import { discoveryModulesMessages } from './discoveryModules'
import { squadOrganizationMessages } from './squadOrganization'
import { fillLocalizedMessages } from '../autoLocalization'
import { groupManagementMessages } from './groupManagement'
import { royalBlackwaterFleetMessages } from './royalBlackwaterFleet'
import { registrationAndInventoryCleanupMessages } from './registrationAndInventoryCleanup'
import { userBuildsAndPasswordMessages } from './userBuildsAndPassword'

const messageLayers = [
  appShellMessages,
  privacyMessages,
  authAdminProfileMessages,
  userBuildsAndPasswordMessages,
  groupManagementMessages,
  newcomerGuideMessages,
  royalBlackwaterFleetMessages,
  contentModulesAndBuildStatsMessages,
  dateFieldFixMessages,
  buildDesignerEquipmentRulesMessages,
  buildEditingAndPreferencesMessages,
  fleetCalendarMessages,
  squadOrganizationMessages,
  mySquadsWorkspaceMessages,
  fleetManagementMessages,
  staffPanelMessages,
  staffWorkspaceOverhaulMessages,
  systemOperationsMessages,
  securityAuditDashboardMessages,
  ipBlockManagementMessages,
  outboundWebhookManagementMessages,
  discordWebhooksMessages,
  discoveryModulesMessages,
  adminDashboardMessages,
  masterDataMessages,
  finalNavigationAndGroupSignupMessages,
  fleetIdentityMessages,
  registrationAndInventoryCleanupMessages,
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
