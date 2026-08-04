-- Generated once from immutable V1 by scripts/migration/generate_modular_flyway_baseline.py.
-- New databases start at B2 and apply this focused schema part. Existing V1 databases
-- execute it safely because CREATE TABLE/INDEX statements are idempotent.
-- Migration responsibility: 4__identity_and_catalog_relations.

CREATE TABLE IF NOT EXISTS users (
	id SERIAL NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	site_role_id INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_bootstrap_admin BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(site_role_id) REFERENCES site_roles (id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS audit_logs (
	id SERIAL NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	actor_user_id INTEGER, 
	actor_username VARCHAR(80) NOT NULL, 
	actor_role VARCHAR(32) NOT NULL, 
	entity_type VARCHAR(40) NOT NULL, 
	entity_id VARCHAR(80) NOT NULL, 
	action VARCHAR(24) NOT NULL, 
	summary VARCHAR(500) NOT NULL, 
	changed_fields_json TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS auth_sessions (
	id SERIAL NOT NULL, 
	token_hash VARCHAR(128) NOT NULL, 
	user_id INTEGER NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS build_item_effects (
	id SERIAL NOT NULL, 
	option_id INTEGER NOT NULL, 
	effect_key VARCHAR(80) NOT NULL, 
	effect_value FLOAT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_item_effect_key UNIQUE (option_id, effect_key), 
	FOREIGN KEY(option_id) REFERENCES build_item_options (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS build_item_option_slot_types (
	id SERIAL NOT NULL, 
	option_id INTEGER NOT NULL, 
	slot_type_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_item_option_slot_type UNIQUE (option_id, slot_type_id), 
	FOREIGN KEY(option_id) REFERENCES build_item_options (id) ON DELETE CASCADE, 
	FOREIGN KEY(slot_type_id) REFERENCES weapon_slot_types (id) ON DELETE CASCADE
);
