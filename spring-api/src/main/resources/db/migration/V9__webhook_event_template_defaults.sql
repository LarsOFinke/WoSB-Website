-- The former catalog exposed one generic value for every event. Webhooks that
-- saved that exact value now unintentionally override the event-specific
-- defaults introduced later. Preserve every administrator-authored template
-- and clear only the known legacy catalog value.
UPDATE outbound_webhooks
SET message_template = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE message_template = 'RBF event **{event}** for {resource.type} #{resource.id}.';
