-- Build printouts are a server-wide derived cache. Keep cache identity separate
-- from the business build revision so storing an image never mutates updated_at.
-- Lookup remains by build primary key; a separate cache-key index would add
-- storage without serving the current access pattern.
ALTER TABLE builds
    ADD COLUMN IF NOT EXISTS printout_cache_key VARCHAR(128),
    ADD COLUMN IF NOT EXISTS printout_source_updated_at TIMESTAMP WITHOUT TIME ZONE;
