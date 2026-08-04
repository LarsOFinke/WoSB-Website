-- Empty version marker for the modular schema path.
-- Fresh databases use this baseline migration instead of the immutable monolithic V1 and then
-- apply V3 through V7. Existing databases with V1 history ignore B2 and safely apply V3 through
-- V7 idempotently, preserving the released V1 checksum and all existing data.
DO $$ BEGIN NULL; END $$;
