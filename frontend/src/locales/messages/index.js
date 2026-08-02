import { cloneMessages, mergeMessages } from '../utils.js'
import { adminDashboardMessages } from './adminDashboard.js'
import { appShellMessages } from './appShell.js'
import { authAdminProfileMessages } from './authAdminProfile.js'
import { baseMessages } from './base.js'
import { backupManagementMessages } from './backupManagement.js'
import { backupRecoveryExtensionMessages } from './backupRecoveryExtensions.js'
import { buildDesignerEquipmentRulesMessages } from './buildDesignerEquipmentRules.js'
import { buildEditingAndPreferencesMessages } from './buildEditingAndPreferences.js'
import { buildVotingRolesAndSearchMessages } from './buildVotingRolesAndSearch.js'
import { contentModulesAndBuildStatsMessages } from './contentModulesAndBuildStats.js'
import { combatAnalysisMessages } from './combatAnalysis.js'
import { dateFieldFixMessages } from './dateFieldFixes.js'
import { dataRightsMessages } from './dataRights.js'
import { fleetCalendarMessages } from './fleetCalendar.js'
import { fleetIdentityMessages } from './fleetIdentity.js'
import { fleetManagementMessages } from './fleetManagement.js'
import { finalNavigationAndGroupSignupMessages } from './finalNavigationAndGroupSignup.js'
import { localeCompletenessMessages } from './localeCompleteness.js'
import { legalNoticeMessages } from './legalNotice.js'
import { newcomerGuideMessages } from './newcomerGuide.js'
import { mySquadsWorkspaceMessages } from './mySquadsWorkspace.js'
import { privacyMessages } from './privacy.js'
import { privacyCenterMessages } from './privacyCenter.js'
import { masterDataMessages } from './masterData.js'
import { staffPanelMessages } from './staffPanel.js'
import { staffWorkspaceOverhaulMessages } from './staffWorkspaceOverhaul.js'
import { systemOperationsMessages } from './systemOperations.js'
import { systemLogManagementMessages } from './systemLogManagement.js'
import { securityAuditDashboardMessages } from './securityAuditDashboard.js'
import { ipBlockManagementMessages } from './ipBlockManagement.js'
import { outboundWebhookManagementMessages } from './outboundWebhookManagement.js'
import { discordWebhooksMessages } from './discordWebhooks.js'
import { discoveryModulesMessages } from './discoveryModules.js'
import { squadOrganizationMessages } from './squadOrganization.js'
import { fillLocalizedMessages } from '../autoLocalization.js'
import { groupManagementMessages } from './groupManagement.js'
import { royalBlackwaterFleetMessages } from './royalBlackwaterFleet.js'
import { registrationAndInventoryCleanupMessages } from './registrationAndInventoryCleanup.js'
import { raidHelperMessages } from './raidHelper.js'
import { userBuildsAndPasswordMessages } from './userBuildsAndPassword.js'

const messageLayers = [
  appShellMessages,
  privacyMessages,
  privacyCenterMessages,
  dataRightsMessages,
  legalNoticeMessages,
  authAdminProfileMessages,
  userBuildsAndPasswordMessages,
  groupManagementMessages,
  newcomerGuideMessages,
  royalBlackwaterFleetMessages,
  contentModulesAndBuildStatsMessages,
  combatAnalysisMessages,
  dateFieldFixMessages,
  buildDesignerEquipmentRulesMessages,
  buildEditingAndPreferencesMessages,
  buildVotingRolesAndSearchMessages,
  backupManagementMessages,
  backupRecoveryExtensionMessages,
  fleetCalendarMessages,
  squadOrganizationMessages,
  mySquadsWorkspaceMessages,
  fleetManagementMessages,
  staffPanelMessages,
  staffWorkspaceOverhaulMessages,
  systemOperationsMessages,
  systemLogManagementMessages,
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
  raidHelperMessages,
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
