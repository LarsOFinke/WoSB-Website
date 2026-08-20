CREATE TABLE warehouse_entries (
    id BIGSERIAL PRIMARY KEY,
    fleet_id INTEGER NOT NULL REFERENCES fleets(id) ON DELETE CASCADE,
    member_user_id INTEGER REFERENCES users(id) ON DELETE RESTRICT,
    custom_holder_name VARCHAR(120),
    port VARCHAR(120) NOT NULL,
    resource VARCHAR(120) NOT NULL,
    amount BIGINT NOT NULL DEFAULT 0,
    reserved BOOLEAN NOT NULL DEFAULT FALSE,
    version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT warehouse_holder_source_check CHECK (
        (member_user_id IS NOT NULL AND custom_holder_name IS NULL)
        OR (member_user_id IS NULL AND custom_holder_name IS NOT NULL)
    ),
    CONSTRAINT warehouse_custom_holder_name_check CHECK (
        custom_holder_name IS NULL OR length(btrim(custom_holder_name)) BETWEEN 1 AND 120
    ),
    CONSTRAINT warehouse_port_check CHECK (length(btrim(port)) BETWEEN 1 AND 120),
    CONSTRAINT warehouse_resource_check CHECK (length(btrim(resource)) BETWEEN 1 AND 120),
    CONSTRAINT warehouse_amount_check CHECK (amount BETWEEN 0 AND 999999999),
    CONSTRAINT warehouse_version_check CHECK (version >= 1)
);

CREATE INDEX warehouse_entries_fleet_filter_idx
    ON warehouse_entries(fleet_id, lower(port), lower(resource), reserved);

CREATE INDEX warehouse_entries_member_idx
    ON warehouse_entries(member_user_id)
    WHERE member_user_id IS NOT NULL;
