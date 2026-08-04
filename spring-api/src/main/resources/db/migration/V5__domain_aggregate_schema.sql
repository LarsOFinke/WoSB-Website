-- Generated once from immutable V1 by scripts/migration/generate_modular_flyway_baseline.py.
-- New databases start at B2 and apply this focused schema part. Existing V1 databases
-- execute it safely because CREATE TABLE/INDEX statements are idempotent.
-- Migration responsibility: 5__domain_aggregate_schema.

CREATE TABLE IF NOT EXISTS builds (
	id SERIAL NOT NULL, 
	build_name VARCHAR(140) NOT NULL, 
	build_type VARCHAR(32) NOT NULL, 
	ship_id INTEGER NOT NULL, 
	owner_id INTEGER, 
	is_official_template BOOLEAN NOT NULL, 
	research_upgrade_feature_id INTEGER, 
	mortar_modification_installed BOOLEAN NOT NULL, 
	sailors INTEGER NOT NULL, 
	soldiers INTEGER NOT NULL, 
	musketeers INTEGER NOT NULL, 
	mercenaries INTEGER NOT NULL, 
	details TEXT, 
	printout_checksum VARCHAR(64), 
	printout_size_bytes BIGINT, 
	printout_updated_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_builds_sailors CHECK (sailors >= 0), 
	CONSTRAINT ck_builds_soldiers CHECK (soldiers >= 0), 
	CONSTRAINT ck_builds_musketeers CHECK (musketeers >= 0), 
	CONSTRAINT ck_builds_mercenaries CHECK (mercenaries >= 0), 
	FOREIGN KEY(build_type) REFERENCES build_roles (slug) ON DELETE RESTRICT ON UPDATE RESTRICT, 
	FOREIGN KEY(ship_id) REFERENCES ships (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	FOREIGN KEY(research_upgrade_feature_id) REFERENCES build_features (id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS cookie_consent_decisions (
	id SERIAL NOT NULL, 
	consent_key VARCHAR(64) NOT NULL, 
	user_id INTEGER, 
	policy_version VARCHAR(32) NOT NULL, 
	necessary BOOLEAN NOT NULL, 
	preferences BOOLEAN NOT NULL, 
	analytics BOOLEAN NOT NULL, 
	external_media BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS data_subject_requests (
	id SERIAL NOT NULL, 
	subject_user_id INTEGER NOT NULL, 
	request_type VARCHAR(24) NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	details TEXT, 
	resolution_note TEXT, 
	handled_by_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(subject_user_id) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(handled_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS fleet_memberships (
	id SERIAL NOT NULL, 
	fleet_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	fleet_role_id INTEGER NOT NULL, 
	status VARCHAR(40) NOT NULL, 
	note TEXT, 
	assignment VARCHAR(120), 
	admin_note TEXT, 
	joined_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_fleet_membership_user UNIQUE (fleet_id, user_id), 
	CONSTRAINT uq_fleet_membership_single_user UNIQUE (user_id), 
	CONSTRAINT ck_fleet_memberships_status CHECK (status in ('pending', 'active', 'inactive')), 
	FOREIGN KEY(fleet_id) REFERENCES fleets (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(fleet_role_id) REFERENCES fleet_roles (id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS forum_threads (
	id SERIAL NOT NULL, 
	title VARCHAR(160) NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	owner_id INTEGER NOT NULL, 
	is_pinned BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
);


CREATE TABLE IF NOT EXISTS groups (
	id SERIAL NOT NULL, 
	title VARCHAR(140) NOT NULL, 
	focus VARCHAR(80) NOT NULL, 
	description TEXT, 
	expectations TEXT, 
	activity_plan TEXT, 
	contact_note VARCHAR(300), 
	scheduled_start_at TIMESTAMP WITHOUT TIME ZONE, 
	scheduled_end_at TIMESTAMP WITHOUT TIME ZONE, 
	max_members INTEGER NOT NULL, 
	min_ship_rate INTEGER, 
	max_ship_rate INTEGER, 
	allow_guests BOOLEAN NOT NULL, 
	fleet_restriction VARCHAR(120), 
	status VARCHAR(32) NOT NULL, 
	owner_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_groups_status CHECK (status in ('open', 'full', 'closed')), 
	CONSTRAINT ck_groups_max_members CHECK (max_members >= 2 and max_members <= 50), 
	CONSTRAINT ck_groups_min_ship_rate CHECK (min_ship_rate is null or (min_ship_rate >= 1 and min_ship_rate <= 7)), 
	CONSTRAINT ck_groups_max_ship_rate CHECK (max_ship_rate is null or (max_ship_rate >= 1 and max_ship_rate <= 7)), 
	CONSTRAINT ck_groups_schedule_range CHECK (scheduled_end_at is null or scheduled_start_at is null or scheduled_end_at > scheduled_start_at), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
);


CREATE TABLE IF NOT EXISTS guides (
	id SERIAL NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	summary VARCHAR(400), 
	body TEXT NOT NULL, 
	owner_id INTEGER NOT NULL, 
	is_published BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
);


CREATE TABLE IF NOT EXISTS ip_blocks (
	id SERIAL NOT NULL, 
	ip_address VARCHAR(45) NOT NULL, 
	reason VARCHAR(240) NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by_user_id INTEGER, 
	created_by_username VARCHAR(80) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	unblocked_at TIMESTAMP WITHOUT TIME ZONE, 
	unblocked_by_user_id INTEGER, 
	unblocked_by_username VARCHAR(80), 
	unblock_reason VARCHAR(240), 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(unblocked_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS newcomer_guide_pages (
	id SERIAL NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	intro TEXT NOT NULL, 
	updated_by_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(updated_by_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS outbound_webhooks (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	endpoint_url TEXT NOT NULL, 
	event_types_json TEXT NOT NULL, 
	scope_type VARCHAR(24) NOT NULL, 
	scope_id INTEGER, 
	message_template TEXT, 
	discord_username VARCHAR(80), 
	broadcast_enabled BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by_user_id INTEGER, 
	created_by_username VARCHAR(80) NOT NULL, 
	last_success_at TIMESTAMP WITHOUT TIME ZONE, 
	last_failure_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS privacy_contact_requests (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	reply_email VARCHAR(254) NOT NULL, 
	subject VARCHAR(160) NOT NULL, 
	message TEXT NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	resolution_note TEXT, 
	handled_by_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(handled_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS raid_helper_template_categories (
	template_id INTEGER NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	PRIMARY KEY (template_id, category), 
	FOREIGN KEY(template_id) REFERENCES raid_helper_templates (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS registration_requests (
	id SERIAL NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	display_name VARCHAR(120) NOT NULL, 
	wants_fleet_membership BOOLEAN NOT NULL, 
	fleet_id INTEGER, 
	fleet_application_note TEXT, 
	status VARCHAR(24) NOT NULL, 
	decision_note TEXT, 
	reviewed_by_id INTEGER, 
	created_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_registration_requests_status CHECK (status in ('pending', 'approved', 'rejected')), 
	FOREIGN KEY(fleet_id) REFERENCES fleets (id) ON DELETE SET NULL, 
	FOREIGN KEY(reviewed_by_id) REFERENCES users (id), 
	FOREIGN KEY(created_user_id) REFERENCES users (id)
);


CREATE TABLE IF NOT EXISTS ship_upgrade_effect_overrides (
	id SERIAL NOT NULL, 
	ship_id INTEGER NOT NULL, 
	option_id INTEGER NOT NULL, 
	effect_key VARCHAR(80) NOT NULL, 
	effect_value FLOAT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_ship_upgrade_effect_override UNIQUE (ship_id, option_id, effect_key), 
	FOREIGN KEY(ship_id) REFERENCES ships (id) ON DELETE CASCADE, 
	FOREIGN KEY(option_id) REFERENCES build_item_options (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS squads (
	id SERIAL NOT NULL, 
	fleet_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	slug VARCHAR(140) NOT NULL, 
	description TEXT, 
	focus VARCHAR(160), 
	max_members INTEGER, 
	is_active BOOLEAN NOT NULL, 
	created_by_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_squads_fleet_name UNIQUE (fleet_id, name), 
	CONSTRAINT uq_squads_fleet_slug UNIQUE (fleet_id, slug), 
	FOREIGN KEY(fleet_id) REFERENCES fleets (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS stored_files (
	id SERIAL NOT NULL, 
	owner_id INTEGER, 
	original_name VARCHAR(255) NOT NULL, 
	stored_name VARCHAR(255) NOT NULL, 
	relative_path VARCHAR(500) NOT NULL, 
	mime_type VARCHAR(120) NOT NULL, 
	size_bytes INTEGER NOT NULL, 
	usage_context VARCHAR(40) NOT NULL, 
	is_public BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	UNIQUE (relative_path)
);


CREATE TABLE IF NOT EXISTS user_profiles (
	user_id INTEGER NOT NULL, 
	display_name VARCHAR(120) NOT NULL, 
	external_fleet_name VARCHAR(120), 
	preferred_focus VARCHAR(80), 
	availability VARCHAR(240), 
	timezone VARCHAR(80), 
	discord_handle VARCHAR(120), 
	note TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS weapon_performance_profiles (
	option_id INTEGER NOT NULL, 
	base_damage FLOAT NOT NULL, 
	reload_seconds FLOAT NOT NULL, 
	PRIMARY KEY (option_id), 
	CONSTRAINT ck_weapon_performance_damage CHECK (base_damage >= 0), 
	CONSTRAINT ck_weapon_performance_reload CHECK (reload_seconds > 0), 
	FOREIGN KEY(option_id) REFERENCES build_item_options (id) ON DELETE CASCADE
);
