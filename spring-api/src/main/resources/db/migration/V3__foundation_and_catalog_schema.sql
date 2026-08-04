-- Generated once from immutable V1 by scripts/migration/generate_modular_flyway_baseline.py.
-- New databases start at B2 and apply this focused schema part. Existing V1 databases
-- execute it safely because CREATE TABLE/INDEX statements are idempotent.
-- Migration responsibility: 3__foundation_and_catalog_schema.

CREATE TABLE IF NOT EXISTS build_features (
	id SERIAL NOT NULL, 
	code VARCHAR(64) NOT NULL, 
	label VARCHAR(120) NOT NULL, 
	upgrade_slots_granted INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_build_features_upgrade_slots_granted CHECK (upgrade_slots_granted >= 0 and upgrade_slots_granted <= 8)
);


CREATE TABLE IF NOT EXISTS build_item_categories (
	id SERIAL NOT NULL, 
	key VARCHAR(40) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	seed_key VARCHAR(220), 
	seed_revision VARCHAR(80), 
	seed_checksum VARCHAR(64), 
	is_seed_overridden BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_build_item_categories_sort_order CHECK (sort_order >= 0)
);


CREATE TABLE IF NOT EXISTS build_roles (
	slug VARCHAR(32) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	description TEXT, 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (slug)
);


CREATE TABLE IF NOT EXISTS fleet_roles (
	id SERIAL NOT NULL, 
	code VARCHAR(40) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	rank INTEGER NOT NULL, 
	is_leadership BOOLEAN NOT NULL, 
	can_manage_fleet BOOLEAN NOT NULL, 
	can_manage_members BOOLEAN NOT NULL, 
	is_system BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_fleet_roles_rank CHECK (rank >= 0)
);


CREATE TABLE IF NOT EXISTS fleets (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	slug VARCHAR(120) NOT NULL, 
	focus VARCHAR(80) NOT NULL, 
	description TEXT, 
	standing_orders TEXT, 
	sort_order INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS legal_notices (
	id INTEGER NOT NULL, 
	published BOOLEAN NOT NULL, 
	is_customized BOOLEAN NOT NULL, 
	provider_name VARCHAR(200) NOT NULL, 
	legal_form VARCHAR(120) NOT NULL, 
	represented_by VARCHAR(300) NOT NULL, 
	street VARCHAR(200) NOT NULL, 
	postal_code VARCHAR(32) NOT NULL, 
	city VARCHAR(120) NOT NULL, 
	country VARCHAR(120) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	phone VARCHAR(80) NOT NULL, 
	register_name VARCHAR(160) NOT NULL, 
	register_court VARCHAR(200) NOT NULL, 
	register_number VARCHAR(120) NOT NULL, 
	vat_id VARCHAR(80) NOT NULL, 
	business_id VARCHAR(120) NOT NULL, 
	supervisory_authority VARCHAR(500) NOT NULL, 
	editorial_responsible_name VARCHAR(200) NOT NULL, 
	editorial_responsible_street VARCHAR(200) NOT NULL, 
	editorial_responsible_postal_code VARCHAR(32) NOT NULL, 
	editorial_responsible_city VARCHAR(120) NOT NULL, 
	editorial_responsible_country VARCHAR(120) NOT NULL, 
	dispute_resolution_text TEXT NOT NULL, 
	additional_information TEXT NOT NULL, 
	updated_by_username VARCHAR(80) NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_legal_notice_singleton CHECK (id = 1)
);


CREATE TABLE IF NOT EXISTS raid_helper_profiles (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	server_id VARCHAR(32) NOT NULL, 
	api_key_encrypted TEXT NOT NULL, 
	api_base_url VARCHAR(200) NOT NULL, 
	timezone VARCHAR(80) NOT NULL, 
	default_leader_id VARCHAR(32), 
	is_active BOOLEAN NOT NULL, 
	created_by_username VARCHAR(80) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_raid_helper_profiles_name UNIQUE (name)
);


CREATE TABLE IF NOT EXISTS security_signal_buckets (
	id SERIAL NOT NULL, 
	day DATE NOT NULL, 
	client_ip VARCHAR(45) NOT NULL, 
	signal VARCHAR(32) NOT NULL, 
	reason VARCHAR(32) NOT NULL, 
	request_target VARCHAR(180) NOT NULL, 
	event_count INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_security_signal_buckets_signal CHECK (signal IN ('reconnaissance', 'login_failure', 'rate_limit')), 
	CONSTRAINT ck_security_signal_buckets_count CHECK (event_count >= 1), 
	CONSTRAINT uq_security_signal_buckets_dimensions UNIQUE (day, client_ip, signal, reason, request_target)
);


CREATE TABLE IF NOT EXISTS ships (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	rate INTEGER NOT NULL, 
	ship_type VARCHAR(80) NOT NULL, 
	durability INTEGER NOT NULL, 
	speed_min_knots FLOAT NOT NULL, 
	speed_knots FLOAT NOT NULL, 
	maneuverability FLOAT NOT NULL, 
	armor FLOAT NOT NULL, 
	hold_capacity INTEGER NOT NULL, 
	crew_capacity INTEGER NOT NULL, 
	sailor_minimum INTEGER NOT NULL, 
	displacement_tons INTEGER NOT NULL, 
	source VARCHAR(240), 
	image_url VARCHAR(500), 
	sail_slots INTEGER NOT NULL, 
	upgrade_slots INTEGER NOT NULL, 
	has_lantern BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	seed_key VARCHAR(220), 
	seed_revision VARCHAR(80), 
	seed_checksum VARCHAR(64), 
	is_seed_overridden BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_ships_rate CHECK (rate >= 1 and rate <= 7), 
	CONSTRAINT ck_ships_durability CHECK (durability >= 0), 
	CONSTRAINT ck_ships_speed_min_knots CHECK (speed_min_knots >= 0), 
	CONSTRAINT ck_ships_speed_range CHECK (speed_knots >= speed_min_knots), 
	CONSTRAINT ck_ships_maneuverability CHECK (maneuverability >= 0), 
	CONSTRAINT ck_ships_armor CHECK (armor >= 0), 
	CONSTRAINT ck_ships_hold_capacity CHECK (hold_capacity >= 0), 
	CONSTRAINT ck_ships_crew_capacity CHECK (crew_capacity >= 0), 
	CONSTRAINT ck_ships_sailor_minimum CHECK (sailor_minimum >= 0), 
	CONSTRAINT ck_ships_displacement_tons CHECK (displacement_tons >= 0), 
	CONSTRAINT ck_ships_sail_slots CHECK (sail_slots >= 0), 
	CONSTRAINT ck_ships_upgrade_slots CHECK (upgrade_slots >= 0 and upgrade_slots <= 8)
);


CREATE TABLE IF NOT EXISTS site_roles (
	id SERIAL NOT NULL, 
	code VARCHAR(32) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	rank INTEGER NOT NULL, 
	is_staff BOOLEAN NOT NULL, 
	can_manage_system BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_site_roles_rank CHECK (rank >= 0)
);


CREATE TABLE IF NOT EXISTS squad_roles (
	id SERIAL NOT NULL, 
	code VARCHAR(24) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	rank INTEGER NOT NULL, 
	can_manage_roster BOOLEAN NOT NULL, 
	can_manage_events BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_squad_roles_rank CHECK (rank >= 0)
);


CREATE TABLE IF NOT EXISTS weapon_classes (
	id SERIAL NOT NULL, 
	code VARCHAR(24) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	rank INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_weapon_classes_rank CHECK (rank >= 0)
);


CREATE TABLE IF NOT EXISTS weapon_slot_types (
	id SERIAL NOT NULL, 
	code VARCHAR(40) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS build_feature_effects (
	id SERIAL NOT NULL, 
	feature_id INTEGER NOT NULL, 
	effect_key VARCHAR(80) NOT NULL, 
	effect_value FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_feature_effect_key UNIQUE (feature_id, effect_key), 
	FOREIGN KEY(feature_id) REFERENCES build_features (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS build_item_options (
	id SERIAL NOT NULL, 
	category_id INTEGER NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	source VARCHAR(240), 
	notes VARCHAR(500), 
	image_url VARCHAR(500), 
	option_kind VARCHAR(40), 
	weapon_class_id INTEGER, 
	weapon_caliber_inches FLOAT, 
	sort_order INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	seed_key VARCHAR(220), 
	seed_revision VARCHAR(80), 
	seed_checksum VARCHAR(64), 
	is_seed_overridden BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_item_option_category_name UNIQUE (category_id, name), 
	FOREIGN KEY(category_id) REFERENCES build_item_categories (id) ON DELETE CASCADE, 
	FOREIGN KEY(weapon_class_id) REFERENCES weapon_classes (id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS raid_helper_templates (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	raid_template_id VARCHAR(80) NOT NULL, 
	scope_type VARCHAR(16) NOT NULL, 
	title_template VARCHAR(300) NOT NULL, 
	description_template TEXT NOT NULL, 
	announcement_template TEXT NOT NULL, 
	payload_template_json TEXT NOT NULL, 
	uses_premium_features BOOLEAN NOT NULL, 
	is_default BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_raid_helper_template_scope CHECK (scope_type IN ('both', 'fleet', 'squad')), 
	CONSTRAINT uq_raid_helper_template_name UNIQUE (profile_id, name), 
	FOREIGN KEY(profile_id) REFERENCES raid_helper_profiles (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS ship_mortar_modifications (
	ship_id INTEGER NOT NULL, 
	mortar_capacity INTEGER NOT NULL, 
	max_caliber_inches FLOAT NOT NULL, 
	broadside_capacity_delta INTEGER NOT NULL, 
	durability_delta INTEGER NOT NULL, 
	speed_pct FLOAT NOT NULL, 
	maneuverability_delta FLOAT NOT NULL, 
	hold_capacity_pct FLOAT NOT NULL, 
	crew_capacity_delta INTEGER NOT NULL, 
	source VARCHAR(500) NOT NULL, 
	PRIMARY KEY (ship_id), 
	CONSTRAINT ck_ship_mortar_mod_capacity CHECK (mortar_capacity > 0), 
	CONSTRAINT ck_ship_mortar_mod_max_caliber CHECK (max_caliber_inches > 0), 
	CONSTRAINT ck_ship_mortar_mod_broadside_delta CHECK (broadside_capacity_delta <= 0), 
	CONSTRAINT ck_ship_mortar_mod_durability_delta CHECK (durability_delta <= 0), 
	CONSTRAINT ck_ship_mortar_mod_crew_delta CHECK (crew_capacity_delta <= 0), 
	CONSTRAINT ck_ship_mortar_mod_percentage_range CHECK (speed_pct > -100 and hold_capacity_pct > -100), 
	FOREIGN KEY(ship_id) REFERENCES ships (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS ship_rate_weapon_class_rules (
	rate SERIAL NOT NULL, 
	weapon_class_id INTEGER NOT NULL, 
	PRIMARY KEY (rate), 
	CONSTRAINT ck_ship_rate_weapon_class_rate CHECK (rate >= 1 and rate <= 7), 
	FOREIGN KEY(weapon_class_id) REFERENCES weapon_classes (id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS ship_weapon_mounts (
	id SERIAL NOT NULL, 
	ship_id INTEGER NOT NULL, 
	slot_type_id INTEGER NOT NULL, 
	capacity INTEGER NOT NULL, 
	special_weapon_capacity INTEGER NOT NULL, 
	max_weapon_class_id INTEGER, 
	max_caliber_inches FLOAT, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_ship_weapon_mount_slot UNIQUE (ship_id, slot_type_id), 
	CONSTRAINT ck_ship_weapon_mount_capacity CHECK (capacity >= 0), 
	CONSTRAINT ck_ship_weapon_mount_special_capacity CHECK (special_weapon_capacity >= 0 and special_weapon_capacity <= capacity), 
	CONSTRAINT ck_ship_weapon_mount_max_caliber CHECK (max_caliber_inches is null or max_caliber_inches >= 0), 
	FOREIGN KEY(ship_id) REFERENCES ships (id) ON DELETE CASCADE, 
	FOREIGN KEY(slot_type_id) REFERENCES weapon_slot_types (id) ON DELETE RESTRICT, 
	FOREIGN KEY(max_weapon_class_id) REFERENCES weapon_classes (id) ON DELETE RESTRICT
);
