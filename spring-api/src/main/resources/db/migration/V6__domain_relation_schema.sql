-- Generated once from immutable V1 by scripts/migration/generate_modular_flyway_baseline.py.
-- New databases start at B2 and apply this focused schema part. Existing V1 databases
-- execute it safely because CREATE TABLE/INDEX statements are idempotent.
-- Migration responsibility: 6__domain_relation_schema.

CREATE TABLE IF NOT EXISTS build_classifications (
	build_id INTEGER NOT NULL, 
	tag VARCHAR(40) NOT NULL, 
	PRIMARY KEY (build_id, tag), 
	FOREIGN KEY(build_id) REFERENCES builds (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS build_file_attachments (
	id SERIAL NOT NULL, 
	build_id INTEGER NOT NULL, 
	file_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_file_attachment UNIQUE (build_id, file_id), 
	FOREIGN KEY(build_id) REFERENCES builds (id) ON DELETE CASCADE, 
	FOREIGN KEY(file_id) REFERENCES stored_files (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS build_slots (
	id SERIAL NOT NULL, 
	build_id INTEGER NOT NULL, 
	slot_type VARCHAR(40) NOT NULL, 
	slot_index INTEGER NOT NULL, 
	option_id INTEGER NOT NULL, 
	quantity INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_slot_position UNIQUE (build_id, slot_type, slot_index), 
	CONSTRAINT ck_build_slots_slot_index CHECK (slot_index >= 0), 
	CONSTRAINT ck_build_slots_quantity CHECK (quantity is null or quantity >= 1), 
	FOREIGN KEY(build_id) REFERENCES builds (id) ON DELETE CASCADE, 
	FOREIGN KEY(option_id) REFERENCES build_item_options (id)
);


CREATE TABLE IF NOT EXISTS build_votes (
	id SERIAL NOT NULL, 
	build_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_votes_build_user UNIQUE (build_id, user_id), 
	FOREIGN KEY(build_id) REFERENCES builds (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS fleet_events (
	id SERIAL NOT NULL, 
	title VARCHAR(160) NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	description TEXT, 
	location VARCHAR(200), 
	start_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	end_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	all_day BOOLEAN NOT NULL, 
	owner_id INTEGER NOT NULL, 
	squad_id INTEGER, 
	is_cancelled BOOLEAN NOT NULL, 
	raid_helper_enabled BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_fleet_events_time_range CHECK (end_at >= start_at), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	FOREIGN KEY(squad_id) REFERENCES squads (id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS forum_posts (
	id SERIAL NOT NULL, 
	thread_id INTEGER NOT NULL, 
	author_id INTEGER NOT NULL, 
	body TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(thread_id) REFERENCES forum_threads (id) ON DELETE CASCADE, 
	FOREIGN KEY(author_id) REFERENCES users (id)
);


CREATE TABLE IF NOT EXISTS group_members (
	id SERIAL NOT NULL, 
	group_id INTEGER NOT NULL, 
	user_id INTEGER, 
	is_guest BOOLEAN NOT NULL, 
	display_name VARCHAR(120) NOT NULL, 
	fleet_name VARCHAR(120), 
	ship_id INTEGER, 
	build_id INTEGER, 
	ship_name VARCHAR(140), 
	ship_rate INTEGER, 
	note TEXT, 
	is_active BOOLEAN NOT NULL, 
	joined_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	left_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_group_members_ship_rate CHECK (ship_rate is null or (ship_rate >= 1 and ship_rate <= 7)), 
	FOREIGN KEY(group_id) REFERENCES groups (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(ship_id) REFERENCES ships (id), 
	FOREIGN KEY(build_id) REFERENCES builds (id)
);


CREATE TABLE IF NOT EXISTS guide_attachments (
	id SERIAL NOT NULL, 
	guide_id INTEGER NOT NULL, 
	file_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(guide_id) REFERENCES guides (id) ON DELETE CASCADE, 
	FOREIGN KEY(file_id) REFERENCES stored_files (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS guide_build_references (
	id SERIAL NOT NULL, 
	guide_id INTEGER NOT NULL, 
	build_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_guide_build_reference UNIQUE (guide_id, build_id), 
	FOREIGN KEY(guide_id) REFERENCES guides (id) ON DELETE CASCADE, 
	FOREIGN KEY(build_id) REFERENCES builds (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS newcomer_guide_blocks (
	id SERIAL NOT NULL, 
	page_id INTEGER NOT NULL, 
	block_type VARCHAR(24) NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	body TEXT, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(page_id) REFERENCES newcomer_guide_pages (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS outbound_webhook_deliveries (
	id SERIAL NOT NULL, 
	webhook_id INTEGER NOT NULL, 
	delivery_id VARCHAR(64) NOT NULL, 
	event_type VARCHAR(80) NOT NULL, 
	resource_type VARCHAR(50) NOT NULL, 
	resource_id VARCHAR(80) NOT NULL, 
	payload_json TEXT NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	attempts INTEGER NOT NULL, 
	response_status INTEGER, 
	response_body TEXT, 
	error_message TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_attempt_at TIMESTAMP WITHOUT TIME ZONE, 
	delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(webhook_id) REFERENCES outbound_webhooks (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS raid_helper_destinations (
	id SERIAL NOT NULL, 
	profile_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	channel_id VARCHAR(32) NOT NULL, 
	scope_type VARCHAR(16) NOT NULL, 
	squad_id INTEGER, 
	is_default BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_raid_helper_destination_scope CHECK (scope_type IN ('fleet', 'squad')), 
	CONSTRAINT ck_raid_helper_destination_scope_target CHECK ((scope_type = 'fleet' AND squad_id IS NULL) OR (scope_type = 'squad' AND squad_id IS NOT NULL)), 
	FOREIGN KEY(profile_id) REFERENCES raid_helper_profiles (id) ON DELETE CASCADE, 
	FOREIGN KEY(squad_id) REFERENCES squads (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS squad_members (
	id SERIAL NOT NULL, 
	squad_id INTEGER NOT NULL, 
	fleet_membership_id INTEGER NOT NULL, 
	squad_role_id INTEGER NOT NULL, 
	note TEXT, 
	joined_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_squad_members_membership UNIQUE (squad_id, fleet_membership_id), 
	FOREIGN KEY(squad_id) REFERENCES squads (id) ON DELETE CASCADE, 
	FOREIGN KEY(fleet_membership_id) REFERENCES fleet_memberships (id) ON DELETE CASCADE, 
	FOREIGN KEY(squad_role_id) REFERENCES squad_roles (id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS user_profile_role_preferences (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	fleet_role_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_profile_role_preference UNIQUE (user_id, fleet_role_id), 
	FOREIGN KEY(user_id) REFERENCES user_profiles (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(fleet_role_id) REFERENCES fleet_roles (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS user_profile_ship_preferences (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	ship_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_profile_ship_preference UNIQUE (user_id, ship_id), 
	FOREIGN KEY(user_id) REFERENCES user_profiles (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(ship_id) REFERENCES ships (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS forum_post_attachments (
	id SERIAL NOT NULL, 
	post_id INTEGER NOT NULL, 
	file_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(post_id) REFERENCES forum_posts (id) ON DELETE CASCADE, 
	FOREIGN KEY(file_id) REFERENCES stored_files (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS newcomer_guide_resources (
	id SERIAL NOT NULL, 
	block_id INTEGER NOT NULL, 
	resource_type VARCHAR(24) NOT NULL, 
	resource_id INTEGER, 
	label VARCHAR(180), 
	description VARCHAR(500), 
	url VARCHAR(500), 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(block_id) REFERENCES newcomer_guide_blocks (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS raid_helper_destination_categories (
	destination_id INTEGER NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	PRIMARY KEY (destination_id, category), 
	FOREIGN KEY(destination_id) REFERENCES raid_helper_destinations (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS raid_helper_event_links (
	id SERIAL NOT NULL, 
	event_id INTEGER NOT NULL, 
	destination_id INTEGER NOT NULL, 
	template_id INTEGER NOT NULL, 
	leader_id_override VARCHAR(32), 
	external_event_id VARCHAR(64), 
	status VARCHAR(24) NOT NULL, 
	last_operation VARCHAR(16) NOT NULL, 
	attempts INTEGER NOT NULL, 
	response_status INTEGER, 
	error_message TEXT, 
	last_attempt_at TIMESTAMP WITHOUT TIME ZONE, 
	synced_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_raid_helper_event_destination UNIQUE (event_id, destination_id), 
	FOREIGN KEY(event_id) REFERENCES fleet_events (id) ON DELETE CASCADE, 
	FOREIGN KEY(destination_id) REFERENCES raid_helper_destinations (id) ON DELETE RESTRICT, 
	FOREIGN KEY(template_id) REFERENCES raid_helper_templates (id) ON DELETE RESTRICT
);
