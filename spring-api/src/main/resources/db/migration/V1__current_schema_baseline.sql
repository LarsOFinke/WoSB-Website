-- Current production schema baseline generated from the reviewed SQLAlchemy metadata.
-- Existing installations from the retired schema manager must pass the controlled adoption gate
-- before the deployment runner enables Flyway baseline-on-migrate for exactly one migration run.


CREATE TABLE build_features (
	id SERIAL NOT NULL, 
	code VARCHAR(64) NOT NULL, 
	label VARCHAR(120) NOT NULL, 
	upgrade_slots_granted INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_build_features_upgrade_slots_granted CHECK (upgrade_slots_granted >= 0 and upgrade_slots_granted <= 8)
);


CREATE TABLE build_item_categories (
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


CREATE TABLE build_roles (
	slug VARCHAR(32) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	description TEXT, 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (slug)
);


CREATE TABLE fleet_roles (
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


CREATE TABLE fleets (
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


CREATE TABLE legal_notices (
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


CREATE TABLE raid_helper_profiles (
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


CREATE TABLE security_signal_buckets (
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


CREATE TABLE ships (
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


CREATE TABLE site_roles (
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


CREATE TABLE squad_roles (
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


CREATE TABLE weapon_classes (
	id SERIAL NOT NULL, 
	code VARCHAR(24) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	rank INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_weapon_classes_rank CHECK (rank >= 0)
);


CREATE TABLE weapon_slot_types (
	id SERIAL NOT NULL, 
	code VARCHAR(40) NOT NULL, 
	label VARCHAR(80) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE build_feature_effects (
	id SERIAL NOT NULL, 
	feature_id INTEGER NOT NULL, 
	effect_key VARCHAR(80) NOT NULL, 
	effect_value FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_feature_effect_key UNIQUE (feature_id, effect_key), 
	FOREIGN KEY(feature_id) REFERENCES build_features (id) ON DELETE CASCADE
);


CREATE TABLE build_item_options (
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


CREATE TABLE raid_helper_templates (
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


CREATE TABLE ship_mortar_modifications (
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


CREATE TABLE ship_rate_weapon_class_rules (
	rate SERIAL NOT NULL, 
	weapon_class_id INTEGER NOT NULL, 
	PRIMARY KEY (rate), 
	CONSTRAINT ck_ship_rate_weapon_class_rate CHECK (rate >= 1 and rate <= 7), 
	FOREIGN KEY(weapon_class_id) REFERENCES weapon_classes (id) ON DELETE RESTRICT
);


CREATE TABLE ship_weapon_mounts (
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


CREATE TABLE users (
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


CREATE TABLE audit_logs (
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


CREATE TABLE auth_sessions (
	id SERIAL NOT NULL, 
	token_hash VARCHAR(128) NOT NULL, 
	user_id INTEGER NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE build_item_effects (
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


CREATE TABLE build_item_option_slot_types (
	id SERIAL NOT NULL, 
	option_id INTEGER NOT NULL, 
	slot_type_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_item_option_slot_type UNIQUE (option_id, slot_type_id), 
	FOREIGN KEY(option_id) REFERENCES build_item_options (id) ON DELETE CASCADE, 
	FOREIGN KEY(slot_type_id) REFERENCES weapon_slot_types (id) ON DELETE CASCADE
);


CREATE TABLE builds (
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


CREATE TABLE cookie_consent_decisions (
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


CREATE TABLE data_subject_requests (
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


CREATE TABLE fleet_memberships (
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


CREATE TABLE forum_threads (
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


CREATE TABLE groups (
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


CREATE TABLE guides (
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


CREATE TABLE ip_blocks (
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


CREATE TABLE newcomer_guide_pages (
	id SERIAL NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	intro TEXT NOT NULL, 
	updated_by_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(updated_by_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE outbound_webhooks (
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


CREATE TABLE privacy_contact_requests (
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


CREATE TABLE raid_helper_template_categories (
	template_id INTEGER NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	PRIMARY KEY (template_id, category), 
	FOREIGN KEY(template_id) REFERENCES raid_helper_templates (id) ON DELETE CASCADE
);


CREATE TABLE registration_requests (
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


CREATE TABLE ship_upgrade_effect_overrides (
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


CREATE TABLE squads (
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


CREATE TABLE stored_files (
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


CREATE TABLE user_profiles (
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


CREATE TABLE weapon_performance_profiles (
	option_id INTEGER NOT NULL, 
	base_damage FLOAT NOT NULL, 
	reload_seconds FLOAT NOT NULL, 
	PRIMARY KEY (option_id), 
	CONSTRAINT ck_weapon_performance_damage CHECK (base_damage >= 0), 
	CONSTRAINT ck_weapon_performance_reload CHECK (reload_seconds > 0), 
	FOREIGN KEY(option_id) REFERENCES build_item_options (id) ON DELETE CASCADE
);


CREATE TABLE build_classifications (
	build_id INTEGER NOT NULL, 
	tag VARCHAR(40) NOT NULL, 
	PRIMARY KEY (build_id, tag), 
	FOREIGN KEY(build_id) REFERENCES builds (id) ON DELETE CASCADE
);


CREATE TABLE build_file_attachments (
	id SERIAL NOT NULL, 
	build_id INTEGER NOT NULL, 
	file_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_file_attachment UNIQUE (build_id, file_id), 
	FOREIGN KEY(build_id) REFERENCES builds (id) ON DELETE CASCADE, 
	FOREIGN KEY(file_id) REFERENCES stored_files (id) ON DELETE CASCADE
);


CREATE TABLE build_slots (
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


CREATE TABLE build_votes (
	id SERIAL NOT NULL, 
	build_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_build_votes_build_user UNIQUE (build_id, user_id), 
	FOREIGN KEY(build_id) REFERENCES builds (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE fleet_events (
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


CREATE TABLE forum_posts (
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


CREATE TABLE group_members (
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


CREATE TABLE guide_attachments (
	id SERIAL NOT NULL, 
	guide_id INTEGER NOT NULL, 
	file_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(guide_id) REFERENCES guides (id) ON DELETE CASCADE, 
	FOREIGN KEY(file_id) REFERENCES stored_files (id) ON DELETE CASCADE
);


CREATE TABLE guide_build_references (
	id SERIAL NOT NULL, 
	guide_id INTEGER NOT NULL, 
	build_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_guide_build_reference UNIQUE (guide_id, build_id), 
	FOREIGN KEY(guide_id) REFERENCES guides (id) ON DELETE CASCADE, 
	FOREIGN KEY(build_id) REFERENCES builds (id) ON DELETE CASCADE
);


CREATE TABLE newcomer_guide_blocks (
	id SERIAL NOT NULL, 
	page_id INTEGER NOT NULL, 
	block_type VARCHAR(24) NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	body TEXT, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(page_id) REFERENCES newcomer_guide_pages (id) ON DELETE CASCADE
);


CREATE TABLE outbound_webhook_deliveries (
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


CREATE TABLE raid_helper_destinations (
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


CREATE TABLE squad_members (
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


CREATE TABLE user_profile_role_preferences (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	fleet_role_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_profile_role_preference UNIQUE (user_id, fleet_role_id), 
	FOREIGN KEY(user_id) REFERENCES user_profiles (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(fleet_role_id) REFERENCES fleet_roles (id) ON DELETE CASCADE
);


CREATE TABLE user_profile_ship_preferences (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	ship_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_profile_ship_preference UNIQUE (user_id, ship_id), 
	FOREIGN KEY(user_id) REFERENCES user_profiles (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(ship_id) REFERENCES ships (id) ON DELETE CASCADE
);


CREATE TABLE forum_post_attachments (
	id SERIAL NOT NULL, 
	post_id INTEGER NOT NULL, 
	file_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(post_id) REFERENCES forum_posts (id) ON DELETE CASCADE, 
	FOREIGN KEY(file_id) REFERENCES stored_files (id) ON DELETE CASCADE
);


CREATE TABLE newcomer_guide_resources (
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


CREATE TABLE raid_helper_destination_categories (
	destination_id INTEGER NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	PRIMARY KEY (destination_id, category), 
	FOREIGN KEY(destination_id) REFERENCES raid_helper_destinations (id) ON DELETE CASCADE
);


CREATE TABLE raid_helper_event_links (
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

CREATE UNIQUE INDEX ix_build_features_code ON build_features (code);
CREATE INDEX ix_build_item_categories_id ON build_item_categories (id);
CREATE UNIQUE INDEX ix_build_item_categories_key ON build_item_categories (key);
CREATE UNIQUE INDEX ix_build_item_categories_seed_key ON build_item_categories (seed_key);
CREATE INDEX ix_build_roles_sort_order ON build_roles (sort_order);
CREATE UNIQUE INDEX ix_fleet_roles_code ON fleet_roles (code);
CREATE INDEX ix_fleet_roles_is_active ON fleet_roles (is_active);
CREATE INDEX ix_fleet_roles_is_leadership ON fleet_roles (is_leadership);
CREATE INDEX ix_fleet_roles_is_system ON fleet_roles (is_system);
CREATE INDEX ix_fleet_roles_rank ON fleet_roles (rank);
CREATE INDEX ix_fleets_focus ON fleets (focus);
CREATE INDEX ix_fleets_id ON fleets (id);
CREATE UNIQUE INDEX ix_fleets_name ON fleets (name);
CREATE UNIQUE INDEX ix_fleets_slug ON fleets (slug);
CREATE INDEX ix_raid_helper_profiles_is_active ON raid_helper_profiles (is_active);
CREATE INDEX ix_raid_helper_profiles_server_id ON raid_helper_profiles (server_id);
CREATE INDEX ix_security_signal_buckets_client_ip ON security_signal_buckets (client_ip);
CREATE INDEX ix_security_signal_buckets_day ON security_signal_buckets (day);
CREATE INDEX ix_security_signal_buckets_id ON security_signal_buckets (id);
CREATE INDEX ix_security_signal_buckets_signal ON security_signal_buckets (signal);
CREATE INDEX ix_ships_id ON ships (id);
CREATE UNIQUE INDEX ix_ships_name ON ships (name);
CREATE INDEX ix_ships_rate ON ships (rate);
CREATE UNIQUE INDEX ix_ships_seed_key ON ships (seed_key);
CREATE UNIQUE INDEX ix_site_roles_code ON site_roles (code);
CREATE INDEX ix_site_roles_rank ON site_roles (rank);
CREATE UNIQUE INDEX ix_squad_roles_code ON squad_roles (code);
CREATE INDEX ix_squad_roles_rank ON squad_roles (rank);
CREATE UNIQUE INDEX ix_weapon_classes_code ON weapon_classes (code);
CREATE INDEX ix_weapon_classes_rank ON weapon_classes (rank);
CREATE UNIQUE INDEX ix_weapon_slot_types_code ON weapon_slot_types (code);
CREATE INDEX ix_build_feature_effects_effect_key ON build_feature_effects (effect_key);
CREATE INDEX ix_build_feature_effects_feature_id ON build_feature_effects (feature_id);
CREATE INDEX ix_build_item_options_category_id ON build_item_options (category_id);
CREATE INDEX ix_build_item_options_id ON build_item_options (id);
CREATE INDEX ix_build_item_options_name ON build_item_options (name);
CREATE INDEX ix_build_item_options_option_kind ON build_item_options (option_kind);
CREATE UNIQUE INDEX ix_build_item_options_seed_key ON build_item_options (seed_key);
CREATE INDEX ix_build_item_options_weapon_class_id ON build_item_options (weapon_class_id);
CREATE INDEX ix_raid_helper_templates_is_active ON raid_helper_templates (is_active);
CREATE INDEX ix_raid_helper_templates_profile_id ON raid_helper_templates (profile_id);
CREATE INDEX ix_ship_rate_weapon_class_rules_weapon_class_id ON ship_rate_weapon_class_rules (weapon_class_id);
CREATE INDEX ix_ship_weapon_mounts_max_weapon_class_id ON ship_weapon_mounts (max_weapon_class_id);
CREATE INDEX ix_ship_weapon_mounts_ship_id ON ship_weapon_mounts (ship_id);
CREATE INDEX ix_ship_weapon_mounts_slot_type_id ON ship_weapon_mounts (slot_type_id);
CREATE INDEX ix_users_id ON users (id);
CREATE INDEX ix_users_is_bootstrap_admin ON users (is_bootstrap_admin);
CREATE INDEX ix_users_site_role_id ON users (site_role_id);
CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE INDEX ix_audit_logs_action ON audit_logs (action);
CREATE INDEX ix_audit_logs_actor_role ON audit_logs (actor_role);
CREATE INDEX ix_audit_logs_actor_user_id ON audit_logs (actor_user_id);
CREATE INDEX ix_audit_logs_actor_username ON audit_logs (actor_username);
CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX ix_audit_logs_entity_id ON audit_logs (entity_id);
CREATE INDEX ix_audit_logs_entity_type ON audit_logs (entity_type);
CREATE INDEX ix_audit_logs_id ON audit_logs (id);
CREATE INDEX ix_auth_sessions_expires_at ON auth_sessions (expires_at);
CREATE INDEX ix_auth_sessions_id ON auth_sessions (id);
CREATE UNIQUE INDEX ix_auth_sessions_token_hash ON auth_sessions (token_hash);
CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id);
CREATE INDEX ix_build_item_effects_effect_key ON build_item_effects (effect_key);
CREATE INDEX ix_build_item_effects_id ON build_item_effects (id);
CREATE INDEX ix_build_item_effects_option_id ON build_item_effects (option_id);
CREATE INDEX ix_build_item_option_slot_types_option_id ON build_item_option_slot_types (option_id);
CREATE INDEX ix_build_item_option_slot_types_slot_type_id ON build_item_option_slot_types (slot_type_id);
CREATE INDEX ix_builds_build_name ON builds (build_name);
CREATE INDEX ix_builds_build_type ON builds (build_type);
CREATE INDEX ix_builds_id ON builds (id);
CREATE INDEX ix_builds_is_official_template ON builds (is_official_template);
CREATE INDEX ix_builds_owner_id ON builds (owner_id);
CREATE INDEX ix_builds_research_upgrade_feature_id ON builds (research_upgrade_feature_id);
CREATE INDEX ix_builds_ship_id ON builds (ship_id);
CREATE INDEX ix_cookie_consent_decisions_consent_key ON cookie_consent_decisions (consent_key);
CREATE INDEX ix_cookie_consent_decisions_created_at ON cookie_consent_decisions (created_at);
CREATE INDEX ix_cookie_consent_decisions_user_id ON cookie_consent_decisions (user_id);
CREATE INDEX ix_cookie_consent_key_created ON cookie_consent_decisions (consent_key, created_at);
CREATE INDEX ix_data_subject_requests_created_at ON data_subject_requests (created_at);
CREATE INDEX ix_data_subject_requests_request_type ON data_subject_requests (request_type);
CREATE INDEX ix_data_subject_requests_status ON data_subject_requests (status);
CREATE INDEX ix_data_subject_requests_subject_user_id ON data_subject_requests (subject_user_id);
CREATE INDEX ix_fleet_memberships_fleet_id ON fleet_memberships (fleet_id);
CREATE INDEX ix_fleet_memberships_fleet_role_id ON fleet_memberships (fleet_role_id);
CREATE INDEX ix_fleet_memberships_id ON fleet_memberships (id);
CREATE INDEX ix_fleet_memberships_status ON fleet_memberships (status);
CREATE INDEX ix_fleet_memberships_user_id ON fleet_memberships (user_id);
CREATE INDEX ix_forum_threads_category ON forum_threads (category);
CREATE INDEX ix_forum_threads_id ON forum_threads (id);
CREATE INDEX ix_forum_threads_owner_id ON forum_threads (owner_id);
CREATE INDEX ix_forum_threads_title ON forum_threads (title);
CREATE INDEX ix_groups_expires_at ON groups (expires_at);
CREATE INDEX ix_groups_focus ON groups (focus);
CREATE INDEX ix_groups_id ON groups (id);
CREATE INDEX ix_groups_owner_id ON groups (owner_id);
CREATE INDEX ix_groups_scheduled_start_at ON groups (scheduled_start_at);
CREATE INDEX ix_groups_status ON groups (status);
CREATE INDEX ix_groups_title ON groups (title);
CREATE INDEX ix_guides_category ON guides (category);
CREATE INDEX ix_guides_id ON guides (id);
CREATE INDEX ix_guides_is_published ON guides (is_published);
CREATE INDEX ix_guides_owner_id ON guides (owner_id);
CREATE INDEX ix_guides_title ON guides (title);
CREATE INDEX ix_ip_blocks_created_at ON ip_blocks (created_at);
CREATE INDEX ix_ip_blocks_created_by_user_id ON ip_blocks (created_by_user_id);
CREATE INDEX ix_ip_blocks_created_by_username ON ip_blocks (created_by_username);
CREATE INDEX ix_ip_blocks_expires_at ON ip_blocks (expires_at);
CREATE INDEX ix_ip_blocks_id ON ip_blocks (id);
CREATE INDEX ix_ip_blocks_ip_address ON ip_blocks (ip_address);
CREATE INDEX ix_ip_blocks_unblocked_at ON ip_blocks (unblocked_at);
CREATE INDEX ix_ip_blocks_unblocked_by_user_id ON ip_blocks (unblocked_by_user_id);
CREATE INDEX ix_outbound_webhooks_broadcast_enabled ON outbound_webhooks (broadcast_enabled);
CREATE INDEX ix_outbound_webhooks_created_at ON outbound_webhooks (created_at);
CREATE INDEX ix_outbound_webhooks_created_by_user_id ON outbound_webhooks (created_by_user_id);
CREATE INDEX ix_outbound_webhooks_id ON outbound_webhooks (id);
CREATE INDEX ix_outbound_webhooks_is_active ON outbound_webhooks (is_active);
CREATE INDEX ix_outbound_webhooks_name ON outbound_webhooks (name);
CREATE INDEX ix_outbound_webhooks_scope_id ON outbound_webhooks (scope_id);
CREATE INDEX ix_outbound_webhooks_scope_type ON outbound_webhooks (scope_type);
CREATE INDEX ix_outbound_webhooks_updated_at ON outbound_webhooks (updated_at);
CREATE INDEX ix_privacy_contact_requests_created_at ON privacy_contact_requests (created_at);
CREATE INDEX ix_privacy_contact_requests_status ON privacy_contact_requests (status);
CREATE INDEX ix_privacy_contact_requests_user_id ON privacy_contact_requests (user_id);
CREATE INDEX ix_registration_requests_created_at ON registration_requests (created_at);
CREATE INDEX ix_registration_requests_created_user_id ON registration_requests (created_user_id);
CREATE INDEX ix_registration_requests_fleet_id ON registration_requests (fleet_id);
CREATE INDEX ix_registration_requests_id ON registration_requests (id);
CREATE INDEX ix_registration_requests_reviewed_by_id ON registration_requests (reviewed_by_id);
CREATE INDEX ix_registration_requests_status ON registration_requests (status);
CREATE INDEX ix_registration_requests_username ON registration_requests (username);
CREATE INDEX ix_ship_upgrade_effect_overrides_effect_key ON ship_upgrade_effect_overrides (effect_key);
CREATE INDEX ix_ship_upgrade_effect_overrides_id ON ship_upgrade_effect_overrides (id);
CREATE INDEX ix_ship_upgrade_effect_overrides_option_id ON ship_upgrade_effect_overrides (option_id);
CREATE INDEX ix_ship_upgrade_effect_overrides_ship_id ON ship_upgrade_effect_overrides (ship_id);
CREATE INDEX ix_squads_created_by_id ON squads (created_by_id);
CREATE INDEX ix_squads_fleet_id ON squads (fleet_id);
CREATE INDEX ix_squads_id ON squads (id);
CREATE INDEX ix_squads_is_active ON squads (is_active);
CREATE INDEX ix_squads_name ON squads (name);
CREATE INDEX ix_squads_slug ON squads (slug);
CREATE INDEX ix_stored_files_id ON stored_files (id);
CREATE INDEX ix_stored_files_is_public ON stored_files (is_public);
CREATE INDEX ix_stored_files_owner_id ON stored_files (owner_id);
CREATE UNIQUE INDEX ix_stored_files_stored_name ON stored_files (stored_name);
CREATE INDEX ix_stored_files_usage_context ON stored_files (usage_context);
CREATE INDEX ix_build_classifications_tag_build_id ON build_classifications (tag, build_id);
CREATE INDEX ix_build_file_attachments_build_id ON build_file_attachments (build_id);
CREATE INDEX ix_build_file_attachments_file_id ON build_file_attachments (file_id);
CREATE INDEX ix_build_file_attachments_id ON build_file_attachments (id);
CREATE INDEX ix_build_slots_build_id ON build_slots (build_id);
CREATE INDEX ix_build_slots_id ON build_slots (id);
CREATE INDEX ix_build_slots_option_id ON build_slots (option_id);
CREATE INDEX ix_build_slots_slot_type ON build_slots (slot_type);
CREATE INDEX ix_build_votes_build_id ON build_votes (build_id);
CREATE INDEX ix_build_votes_id ON build_votes (id);
CREATE INDEX ix_build_votes_user_id ON build_votes (user_id);
CREATE INDEX ix_fleet_events_active_start ON fleet_events (is_cancelled, start_at, id);
CREATE INDEX ix_fleet_events_category ON fleet_events (category);
CREATE INDEX ix_fleet_events_end_at ON fleet_events (end_at);
CREATE INDEX ix_fleet_events_id ON fleet_events (id);
CREATE INDEX ix_fleet_events_is_cancelled ON fleet_events (is_cancelled);
CREATE INDEX ix_fleet_events_owner_id ON fleet_events (owner_id);
CREATE INDEX ix_fleet_events_raid_helper_enabled ON fleet_events (raid_helper_enabled);
CREATE INDEX ix_fleet_events_squad_active_start ON fleet_events (squad_id, is_cancelled, start_at, id);
CREATE INDEX ix_fleet_events_squad_id ON fleet_events (squad_id);
CREATE INDEX ix_fleet_events_start_at ON fleet_events (start_at);
CREATE INDEX ix_fleet_events_title ON fleet_events (title);
CREATE INDEX ix_forum_posts_author_id ON forum_posts (author_id);
CREATE INDEX ix_forum_posts_id ON forum_posts (id);
CREATE INDEX ix_forum_posts_thread_id ON forum_posts (thread_id);
CREATE INDEX ix_group_members_build_id ON group_members (build_id);
CREATE INDEX ix_group_members_group_id ON group_members (group_id);
CREATE INDEX ix_group_members_id ON group_members (id);
CREATE INDEX ix_group_members_is_active ON group_members (is_active);
CREATE INDEX ix_group_members_ship_id ON group_members (ship_id);
CREATE INDEX ix_group_members_user_id ON group_members (user_id);
CREATE INDEX ix_guide_attachments_file_id ON guide_attachments (file_id);
CREATE INDEX ix_guide_attachments_guide_id ON guide_attachments (guide_id);
CREATE INDEX ix_guide_attachments_id ON guide_attachments (id);
CREATE INDEX ix_guide_build_references_build_id ON guide_build_references (build_id);
CREATE INDEX ix_guide_build_references_guide_id ON guide_build_references (guide_id);
CREATE INDEX ix_guide_build_references_id ON guide_build_references (id);
CREATE INDEX ix_newcomer_guide_blocks_id ON newcomer_guide_blocks (id);
CREATE INDEX ix_newcomer_guide_blocks_page_id ON newcomer_guide_blocks (page_id);
CREATE INDEX ix_outbound_webhook_deliveries_created_at ON outbound_webhook_deliveries (created_at);
CREATE INDEX ix_outbound_webhook_deliveries_delivered_at ON outbound_webhook_deliveries (delivered_at);
CREATE UNIQUE INDEX ix_outbound_webhook_deliveries_delivery_id ON outbound_webhook_deliveries (delivery_id);
CREATE INDEX ix_outbound_webhook_deliveries_event_type ON outbound_webhook_deliveries (event_type);
CREATE INDEX ix_outbound_webhook_deliveries_id ON outbound_webhook_deliveries (id);
CREATE INDEX ix_outbound_webhook_deliveries_last_attempt_at ON outbound_webhook_deliveries (last_attempt_at);
CREATE INDEX ix_outbound_webhook_deliveries_resource_id ON outbound_webhook_deliveries (resource_id);
CREATE INDEX ix_outbound_webhook_deliveries_resource_type ON outbound_webhook_deliveries (resource_type);
CREATE INDEX ix_outbound_webhook_deliveries_status ON outbound_webhook_deliveries (status);
CREATE INDEX ix_outbound_webhook_deliveries_webhook_id ON outbound_webhook_deliveries (webhook_id);
CREATE INDEX ix_webhook_deliveries_created_id ON outbound_webhook_deliveries (created_at, id);
CREATE INDEX ix_webhook_deliveries_status_created_id ON outbound_webhook_deliveries (status, created_at, id);
CREATE INDEX ix_webhook_deliveries_webhook_created_id ON outbound_webhook_deliveries (webhook_id, created_at, id);
CREATE INDEX ix_raid_helper_destinations_is_active ON raid_helper_destinations (is_active);
CREATE INDEX ix_raid_helper_destinations_profile_id ON raid_helper_destinations (profile_id);
CREATE INDEX ix_raid_helper_destinations_scope ON raid_helper_destinations (scope_type, squad_id, is_active);
CREATE INDEX ix_raid_helper_destinations_squad_id ON raid_helper_destinations (squad_id);
CREATE UNIQUE INDEX uq_raid_helper_destinations_fleet_channel ON raid_helper_destinations (profile_id, channel_id) WHERE scope_type = 'fleet';
CREATE UNIQUE INDEX uq_raid_helper_destinations_squad_channel ON raid_helper_destinations (profile_id, channel_id, squad_id) WHERE scope_type = 'squad';
CREATE INDEX ix_squad_members_fleet_membership_id ON squad_members (fleet_membership_id);
CREATE INDEX ix_squad_members_id ON squad_members (id);
CREATE INDEX ix_squad_members_squad_id ON squad_members (squad_id);
CREATE INDEX ix_squad_members_squad_role_id ON squad_members (squad_role_id);
CREATE INDEX ix_user_profile_role_preferences_fleet_role_id ON user_profile_role_preferences (fleet_role_id);
CREATE INDEX ix_user_profile_role_preferences_user_id ON user_profile_role_preferences (user_id);
CREATE INDEX ix_user_profile_ship_preferences_ship_id ON user_profile_ship_preferences (ship_id);
CREATE INDEX ix_user_profile_ship_preferences_user_id ON user_profile_ship_preferences (user_id);
CREATE INDEX ix_forum_post_attachments_file_id ON forum_post_attachments (file_id);
CREATE INDEX ix_forum_post_attachments_id ON forum_post_attachments (id);
CREATE INDEX ix_forum_post_attachments_post_id ON forum_post_attachments (post_id);
CREATE INDEX ix_newcomer_guide_resources_block_id ON newcomer_guide_resources (block_id);
CREATE INDEX ix_newcomer_guide_resources_id ON newcomer_guide_resources (id);
CREATE INDEX ix_raid_helper_event_links_destination_id ON raid_helper_event_links (destination_id);
CREATE INDEX ix_raid_helper_event_links_event_id ON raid_helper_event_links (event_id);
CREATE INDEX ix_raid_helper_event_links_external_event_id ON raid_helper_event_links (external_event_id);
CREATE INDEX ix_raid_helper_event_links_status_updated ON raid_helper_event_links (status, updated_at);
CREATE INDEX ix_raid_helper_event_links_template_id ON raid_helper_event_links (template_id);
