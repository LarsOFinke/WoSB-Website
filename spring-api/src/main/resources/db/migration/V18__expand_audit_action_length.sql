-- Audit action names are part of the internal event contract. Keep enough room
-- for descriptive, stable actions such as enrollment_apply_requested.
ALTER TABLE audit_logs
    ALTER COLUMN action TYPE VARCHAR(64);
