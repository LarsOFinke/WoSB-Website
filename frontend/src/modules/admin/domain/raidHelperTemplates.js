export const RAID_HELPER_CALENDAR_PRESETS = [
  {
    key: 'fleet-calendar',
    scope_type: 'fleet',
    title_template: '⚓ {{event.title}}',
    description_template: '**{{scope.name}}** · {{event.category}}\nStart: {{event.start_at}}\nEnd: {{event.end_at}}\nLocation: {{event.location}}\n\n{{event.description}}',
    announcement_template: 'New fleet event: **{{event.title}}**',
  },
  {
    key: 'squad-calendar',
    scope_type: 'squad',
    title_template: '🛡️ {{scope.name}} · {{event.title}}',
    description_template: '{{event.category}}\nStart: {{event.start_at}}\nEnd: {{event.end_at}}\nLocation: {{event.location}}\n\n{{event.description}}',
    announcement_template: 'New event for **{{scope.name}}**: **{{event.title}}**',
  },
]

export function applyRaidHelperCalendarPreset(form, preset) {
  if (!preset) return
  form.scope_type = preset.scope_type
  form.title_template = preset.title_template
  form.description_template = preset.description_template
  form.announcement_template = preset.announcement_template
}

export const RAID_HELPER_RECOMMENDED_PAYLOAD = `{
  "title": "{{rendered.title}}",
  "description": "{{rendered.description}}",
  "date": "{{event.date}}",
  "time": "{{event.time}}",
  "duration": "{{event.duration_minutes}}",
  "templateId": "{{raid_helper.template_id}}",
  "announcement": "{{rendered.announcement}}",
  "date_variant": "both",
  "12h_format": false,
  "info_variant": "long",
  "preserve_order": true,
  "apply_unregister": true
}`

export function applyRaidHelperRecommendedPayload(form) {
  form.payload_template_json = RAID_HELPER_RECOMMENDED_PAYLOAD
}
