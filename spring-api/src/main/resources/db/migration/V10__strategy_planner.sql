CREATE TABLE strategy_plans (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    background_file_id INTEGER NOT NULL REFERENCES stored_files(id) ON DELETE RESTRICT,
    title VARCHAR(180) NOT NULL,
    description VARCHAR(1000),
    overlay_json TEXT NOT NULL,
    public_id UUID NOT NULL UNIQUE,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    published_at TIMESTAMP WITHOUT TIME ZONE,
    CONSTRAINT ck_strategy_plans_overlay_size CHECK (char_length(overlay_json) <= 200000),
    CONSTRAINT ck_strategy_plans_publication CHECK (
        (is_published = TRUE AND published_at IS NOT NULL)
        OR (is_published = FALSE AND published_at IS NULL)
    )
);

CREATE TABLE strategy_ship_references (
    strategy_id INTEGER NOT NULL REFERENCES strategy_plans(id) ON DELETE CASCADE,
    ship_id INTEGER NOT NULL REFERENCES ships(id) ON DELETE RESTRICT,
    PRIMARY KEY (strategy_id, ship_id)
);

CREATE TABLE strategy_build_references (
    strategy_id INTEGER NOT NULL REFERENCES strategy_plans(id) ON DELETE CASCADE,
    build_id INTEGER NOT NULL REFERENCES builds(id) ON DELETE RESTRICT,
    PRIMARY KEY (strategy_id, build_id)
);

CREATE TABLE strategy_guide_references (
    strategy_id INTEGER NOT NULL REFERENCES strategy_plans(id) ON DELETE CASCADE,
    guide_id INTEGER NOT NULL REFERENCES guides(id) ON DELETE RESTRICT,
    PRIMARY KEY (strategy_id, guide_id)
);

CREATE INDEX ix_strategy_plans_owner_updated ON strategy_plans(owner_id, updated_at DESC);
CREATE INDEX ix_strategy_plans_background_file ON strategy_plans(background_file_id);
CREATE INDEX ix_strategy_ship_references_ship ON strategy_ship_references(ship_id);
CREATE INDEX ix_strategy_build_references_build ON strategy_build_references(build_id);
CREATE INDEX ix_strategy_guide_references_guide ON strategy_guide_references(guide_id);
