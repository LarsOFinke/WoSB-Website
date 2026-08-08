\set ON_ERROR_STOP on

-- Royal Blackwater Fleet logical build-only restore (Java portable v3)
--
-- Source dump: rbf-20260731T074734Z.sql
-- Source SHA-256: c0715c9fe64bdb5e465c56a93ee17ffb845c87b42617f306fb2fd0a4be76c24c
-- Validated against Java seed/runtime model: 1.0.11
--
-- Source content:
--   27 builds
--   625 build slots
--   62 build classifications
--   22 referenced ships
--   85 referenced build options
--   2 referenced build roles
--   1 referenced build feature
--
-- This file intentionally carries BOTH technical and semantic identities:
--
-- Ships:
--   * legacy Python seed_key
--   * current Java seed_key
--   * ship name
--
-- Build options:
--   * legacy Python seed_key
--   * current Java seed_key
--   * category key + option name
--
-- Resolution succeeds only when ALL matching identities point to exactly one
-- target row. Missing or conflicting identities abort the transaction.
--
-- This permits:
--   * old Python seed keys still present in an adopted database,
--   * current Java seed keys,
--   * seeded rows whose technical key was preserved/overridden while the
--     functional name/category remains unchanged.
--
-- It does NOT import or overwrite:
--   users/password hashes, sessions, votes, guides, groups, files, audit data,
--   master-data rows, DDL, constraints, Flyway history or sequences.
--
-- Owners are explicitly mapped by username. Numeric source IDs never cross
-- environments.
--
-- dry_run defaults to 1 and rolls back all changes.
--
-- Test-server example:
--   postgres_sql \
--     -v ON_ERROR_STOP=1 \
--     -v dry_run=1 \
--     -v owner_puszpang=admin \
--     -v owner_nostrapi=admin \
--     -f - < rbf-builds-partial-20260731-java-v3.sql
--
-- Commit after a successful dry-run:
--   same command with -v dry_run=0

\if :{?dry_run}
\else
  \set dry_run 1
\endif

\if :{?owner_admin}
\else
  \set owner_admin admin
\endif
\if :{?owner_puszpang}
\else
  \set owner_puszpang puszpang
\endif
\if :{?owner_nostrapi}
\else
  \set owner_nostrapi nostrapi
\endif

BEGIN;
SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = '5min';

CREATE TEMP TABLE _rbf_owner_map (
    source_username text PRIMARY KEY,
    target_username text NOT NULL
) ON COMMIT DROP;

INSERT INTO _rbf_owner_map(source_username, target_username) VALUES
    ('admin', :'owner_admin'),
    ('puszpang', :'owner_puszpang'),
    ('nostrapi', :'owner_nostrapi');

CREATE TEMP TABLE _rbf_ship_stage (
    source_ship_id integer PRIMARY KEY,
    legacy_seed_key text,
    current_seed_key text NOT NULL,
    ship_name text NOT NULL
) ON COMMIT DROP;

COPY _rbf_ship_stage (
    source_ship_id, legacy_seed_key, current_seed_key, ship_name
) FROM stdin;
1	ship:12 apostolov	ship:12 Apostolov	12 Apostolov
2	ship:de zeven provincien	ship:De Zeven Provincien	De Zeven Provincien
3	ship:huracan	ship:Huracan	Huracan
5	ship:la royale	ship:La Royale	La Royale
7	ship:sovereign	ship:Sovereign	Sovereign
9	ship:adventure	ship:Adventure	Adventure
12	ship:ingermanland	ship:Ingermanland	Ingermanland
17	ship:redoutable	ship:Redoutable	Redoutable
22	ship:azov	ship:Azov	Azov
24	ship:deadfish	ship:Deadfish	Deadfish
26	ship:kobukson	ship:Kobukson	Kobukson
30	ship:poltava	ship:Poltava	Poltava
33	ship:shen	ship:Shen	Shen
34	ship:constitution	ship:Constitution	Constitution
38	ship:flying cloud	ship:Flying Cloud	Flying Cloud
41	ship:red arrow	ship:Red Arrow	Red Arrow
42	ship:sparrow	ship:Sparrow	Sparrow
49	ship:eagle	ship:Eagle	Eagle
54	ship:san martin	ship:San Martin	San Martin
57	ship:golden apostle	ship:Golden Apostle	Golden Apostle
62	ship:polacca	ship:Polacca	Polacca
64	ship:shunsen	ship:Shunsen	Shunsen
\.

CREATE TEMP TABLE _rbf_option_stage (
    source_option_id integer PRIMARY KEY,
    legacy_seed_key text,
    current_seed_key text NOT NULL,
    category_key text NOT NULL,
    option_name text NOT NULL
) ON COMMIT DROP;

COPY _rbf_option_stage (
    source_option_id, legacy_seed_key, current_seed_key,
    category_key, option_name
) FROM stdin;
3	build-option:sail:raiding	option:sail:raiding	sail	Raiding Sails
10	build-option:upgrade:advanced-gun-carriages	option:upgrade:advanced-gun-carriages	upgrade	Advanced Gun Carriages
11	build-option:upgrade:ammunition-cradles	option:upgrade:ammunition-cradles	upgrade	Ammunition Cradles
14	build-option:upgrade:combat-crow-s-nest	option:upgrade:combat-crow-s-nest	upgrade	Combat Crow's Nest
15	build-option:upgrade:copper-plating	option:upgrade:copper-plating	upgrade	Copper Plating
19	build-option:upgrade:extra-bunks	option:upgrade:extra-bunks	upgrade	Extra Bunks
20	build-option:upgrade:fortified-ports	option:upgrade:fortified-ports	upgrade	Fortified Ports
22	build-option:upgrade:incendiary-mixture	option:upgrade:incendiary-mixture	upgrade	Incendiary Mixture
23	build-option:upgrade:iron-plating	option:upgrade:iron-plating	upgrade	Iron Plating
25	build-option:upgrade:lightweight-construction	option:upgrade:lightweight-construction	upgrade	Lightweight Construction
26	build-option:upgrade:lightweight-hull	option:upgrade:lightweight-hull	upgrade	Lightweight Hull
27	build-option:upgrade:long-range-mortars	option:upgrade:long-range-mortars	upgrade	Long-Range Mortars
30	build-option:upgrade:reinforced-bolt-ropes	option:upgrade:reinforced-bolt-ropes	upgrade	Reinforced Bolt Ropes
31	build-option:upgrade:reinforced-cannons	option:upgrade:reinforced-cannons	upgrade	Reinforced Cannons
33	build-option:upgrade:reinforced-masts	option:upgrade:reinforced-masts	upgrade	Reinforced Masts
34	build-option:upgrade:repair-arsenal	option:upgrade:repair-arsenal	upgrade	Repair Arsenal
36	build-option:upgrade:strong-beams	option:upgrade:strong-beams	upgrade	Strong Beams
37	build-option:upgrade:structural-expansion	option:upgrade:structural-expansion	upgrade	Structural Expansion
38	build-option:upgrade:sturdy-frames	option:upgrade:sturdy-frames	upgrade	Sturdy Frames
39	build-option:upgrade:swivel-mortars	option:upgrade:swivel-mortars	upgrade	Swivel Mortars
40	build-option:upgrade:teak-frames	option:upgrade:teak-frames	upgrade	Teak Frames
44	build-option:lantern:golden	option:lantern:golden	lantern	Golden Lantern
45	build-option:lantern:green	option:lantern:green	lantern	Green Lantern
48	build-option:lantern:red	option:lantern:red	lantern	Red Lantern
50	build-option:lantern:yellow	option:lantern:yellow	lantern	Yellow Lantern
51	build-option:ammunition:bar-shots	option:ammunition:bar-shots	ammunition	Bar Shots
52	build-option:ammunition:burning-arrows	option:ammunition:burning-arrows	ammunition	Burning Arrows
54	build-option:ammunition:grapeshot	option:ammunition:grapeshot	ammunition	Grapeshot
55	build-option:ammunition:heated-shots	option:ammunition:heated-shots	ammunition	Heated Shots
56	build-option:ammunition:large-phosphorous-mine	option:ammunition:large-phosphorous-mine	ammunition	Large Phosphorous Mine
58	build-option:ammunition:phosphorous-shots	option:ammunition:phosphorous-shots	ammunition	Phosphorous Shots
59	build-option:ammunition:round-shots	option:ammunition:round-shots	ammunition	Round Shots
61	build-option:ammunition:small-flaming-barrels	option:ammunition:small-flaming-barrels	ammunition	Small Flaming Barrels
62	build-option:ammunition:small-gunpowder-barrels	option:ammunition:small-gunpowder-barrels	ammunition	Small Gunpowder Barrels
63	build-option:ammunition:small-phosphorous-barrels	option:ammunition:small-phosphorous-barrels	ammunition	Small Phosphorous Barrels
64	build-option:ammunition:strike-rounds	option:ammunition:strike-rounds	ammunition	Strike Rounds
66	build-option:consumable:blue-signal-flare	option:consumable:blue-signal-flare	consumable	Blue Signal Flare
68	build-option:consumable:bronze-patches	option:consumable:bronze-patches	consumable	Bronze Patches
69	build-option:consumable:bronze-repair-kit	option:consumable:bronze-repair-kit	consumable	Bronze Repair Kit
71	build-option:consumable:filling-ration	option:consumable:filling-ration	consumable	Filling Ration
73	build-option:consumable:iron-patches	option:consumable:iron-patches	consumable	Iron Patches
75	build-option:consumable:large-additional-sails	option:consumable:large-additional-sails	consumable	Large Additional Sails
76	build-option:consumable:large-plates	option:consumable:large-plates	consumable	Large Plates
77	build-option:consumable:phosphorous	option:consumable:phosphorous	consumable	Phosphorous
82	build-option:consumable:rum-ration	option:consumable:rum-ration	consumable	Rum Ration
84	build-option:consumable:small-plates	option:consumable:small-plates	consumable	Small Plates
86	build-option:consumable:smoke-screen	option:consumable:smoke-screen	consumable	Smoke Screen
87	build-option:consumable:white-double-powder	option:consumable:white-double-powder	consumable	White Double Powder
105	build-option:hold:fabric	option:hold:fabric	hold	Fabric
107	build-option:hold:fresh-meat	option:hold:fresh-meat	hold	Fresh Meat
127	build-option:hold:supplies	option:hold:supplies	hold	Supplies
134	build-option:hold:wood	option:hold:wood	hold	Wood
137	build-option:weapon:11-inch-mortar	option:weapon:11-inch-mortar	weapon	11-inch Mortar
145	build-option:weapon:22-pdr-scorcher	option:weapon:22-pdr-scorcher	weapon	22-pdr Scorcher
147	build-option:weapon:28-pdr-carronade	option:weapon:28-pdr-carronade	weapon	28-pdr Carronade
148	build-option:weapon:32-pdr-cannon	option:weapon:32-pdr-cannon	weapon	32-pdr Cannon
149	build-option:weapon:32-pdr-long-cannon	option:weapon:32-pdr-long-cannon	weapon	32-pdr Long Cannon
152	build-option:weapon:38-pdr-jericho	option:weapon:38-pdr-jericho	weapon	38-pdr Jericho
155	build-option:weapon:6-inch-mortar	option:weapon:6-inch-mortar	weapon	6-inch Mortar
158	build-option:weapon:7-inch-mortar	option:weapon:7-inch-mortar	weapon	7-inch Mortar
159	build-option:weapon:8-inch-mortar	option:weapon:8-inch-mortar	weapon	8-inch Mortar
161	build-option:weapon:8-pdr-culverin	option:weapon:8-pdr-culverin	weapon	8-pdr Culverin
164	build-option:weapon:barrel-launcher	option:weapon:barrel-launcher	weapon	Barrel Launcher
166	build-option:weapon:gilgamesh	option:weapon:gilgamesh	weapon	Gilgamesh
168	build-option:weapon:imperial-bombard	option:weapon:imperial-bombard	weapon	Imperial Bombard
169	build-option:weapon:mjolnir	option:weapon:mjolnir	weapon	Mjolnir
173	build-option:weapon:triple-16-pdr	option:weapon:triple-16-pdr	weapon	Triple 16-pdr
177	build-option:weapon:zeus	option:weapon:zeus	weapon	Zeus
178	build-option:special_crew:armorer	option:special_crew:armorer	special_crew	Armorer
179	build-option:special_crew:artillerist	option:special_crew:artillerist	special_crew	Artillerist
183	build-option:special_crew:commodore	option:special_crew:commodore	special_crew	Commodore
186	build-option:special_crew:daredevil	option:special_crew:daredevil	special_crew	Daredevil
187	build-option:special_crew:surgeon	option:special_crew:surgeon	special_crew	Doctor
189	build-option:special_crew:first-mate	option:special_crew:first-mate	special_crew	First Mate
192	build-option:special_crew:gunner	option:special_crew:gunner	special_crew	Gunner
198	build-option:special_crew:mastman	option:special_crew:mastman	special_crew	Mastman
207	build-option:special_crew:sailmaker	option:special_crew:sailmaker	special_crew	Sail Handler
216	build-option:special_crew:sub-lieutenant	option:special_crew:sub-lieutenant	special_crew	Sub-lieutenant
219	build-option:special_crew:watchman	option:special_crew:watchman	special_crew	Watchman
220	build-option:special_crew:bombardier	option:special_crew:bombardier	special_crew	Bombardier
222	build-option:special_crew:crew-carpenter	option:special_crew:crew-carpenter	special_crew	Carpenter
224	build-option:special_crew:pilot	option:special_crew:pilot	special_crew	Pilot
225	build-option:special_crew:provost	option:special_crew:provost	special_crew	Provost
229	build-option:ammunition:heavy-shots	option:ammunition:heavy-shots	ammunition	Heavy Shots
230	build-option:ammunition:saxon-shots	option:ammunition:saxon-shots	ammunition	Saxon Shots
\.

CREATE TEMP TABLE _rbf_build_stage (
    old_build_id integer PRIMARY KEY,
    build_name varchar(140) NOT NULL,
    build_type varchar(32) NOT NULL,
    source_ship_id integer NOT NULL,
    owner_username text,
    is_official_template boolean NOT NULL,
    sailors integer NOT NULL,
    soldiers integer NOT NULL,
    musketeers integer NOT NULL,
    mercenaries integer NOT NULL,
    details text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    mortar_modification_installed boolean NOT NULL,
    research_feature_code text
) ON COMMIT DROP;

COPY _rbf_build_stage (
    old_build_id, build_name, build_type, source_ship_id, owner_username,
    is_official_template, sailors, soldiers, musketeers, mercenaries,
    details, created_at, updated_at, mortar_modification_installed,
    research_feature_code
) FROM stdin;
4	Flying Cloud BMark-Mine Run 1 Hour	defensive	38	nostrapi	f	100	0	0	0	\N	2026-07-26 20:22:38.235992	2026-07-26 20:22:38.236014	f	\N
5	Zeven - DPS/Boarding	gunnery	2	admin	f	102	90	30	0	Don't force changeing sides and try to keep yourself angled as much as possible to avoid damage intake.\nZeven is a mitigator, not a full-tank.\n\nFor PvP swap side-cannons to Inrogs and change consumables to be:\n- Large Additional Sails\n- Phosphorus\n- Bronze Patches	2026-07-28 08:29:44.622422	2026-07-28 08:51:58.985728	f	\N
6	Huracan Port Battle Tank	defensive	3	puszpang	f	302	0	0	0	\N	2026-07-29 12:39:19.074204	2026-07-29 12:39:19.074225	f	\N
7	12 Apostolov Port Battle DPS	gunnery	1	puszpang	f	234	0	0	0	\N	2026-07-29 18:34:02.321338	2026-07-29 18:34:02.32136	f	\N
8	La Royale Port Battle Mortar	gunnery	5	puszpang	f	156	0	0	0	\N	2026-07-29 18:42:48.519239	2026-07-29 18:42:48.519262	f	\N
9	Sovereign Port Battle Barrel	gunnery	7	puszpang	f	192	0	0	0	\N	2026-07-29 18:48:47.821122	2026-07-29 18:48:47.821146	f	\N
10	Redoutable Port Battle Tank	defensive	17	puszpang	f	212	0	0	0	\N	2026-07-29 18:58:46.453511	2026-07-29 18:58:46.453536	f	\N
11	Redoutable Port Battle DPS	gunnery	17	puszpang	f	212	0	0	0	\N	2026-07-29 19:03:08.418672	2026-07-29 19:03:08.418695	f	\N
12	Shen Port Battle Mortar	gunnery	33	puszpang	f	158	0	0	0	\N	2026-07-29 19:09:13.575542	2026-07-29 19:09:13.575564	f	\N
13	Adventure Port Battle Barrel	gunnery	9	puszpang	f	140	0	0	0	\N	2026-07-29 19:15:46.800447	2026-07-29 19:15:46.800479	f	\N
14	Deadfish Portbattle Tank	defensive	24	puszpang	f	176	0	0	0	\N	2026-07-29 19:26:23.307978	2026-07-29 19:26:23.308003	f	\N
15	Azov Port Battle DPS	gunnery	22	puszpang	f	178	0	0	0	\N	2026-07-29 19:32:05.799358	2026-07-29 19:32:05.79938	f	\N
16	Kobukson Port Battle Barrel	gunnery	26	puszpang	f	124	0	0	0	\N	2026-07-29 19:39:03.699864	2026-07-29 19:39:03.699893	f	\N
17	Constitution Port Battle Tank	defensive	34	puszpang	f	158	0	0	0	\N	2026-07-29 19:45:57.839398	2026-07-29 19:45:57.839429	f	\N
18	Constitution Port Battle DPS	gunnery	34	puszpang	f	158	0	0	0	\N	2026-07-29 19:49:02.317387	2026-07-29 19:49:02.317418	f	\N
19	Sparrow Port Battle Mortar	gunnery	42	puszpang	f	72	0	0	0	\N	2026-07-29 20:00:36.556497	2026-07-29 20:00:36.556521	f	\N
20	Red Arrow Port Battle Barrel	gunnery	41	puszpang	f	140	0	0	0	\N	2026-07-29 20:05:49.988291	2026-07-29 20:05:49.988314	f	\N
21	San Martin Port Battle Tank	defensive	54	puszpang	f	132	0	0	0	\N	2026-07-29 20:13:27.594099	2026-07-29 20:13:27.594122	f	\N
22	San Martin Port Battle DPS	gunnery	54	puszpang	f	132	0	0	0	\N	2026-07-29 20:16:46.096048	2026-07-29 20:16:46.096081	f	\N
23	Eagle Port Battle Mortar	gunnery	49	puszpang	f	84	0	0	0	\N	2026-07-29 20:30:05.579547	2026-07-29 20:30:05.57957	f	\N
24	Eagle Port Battle Barrel	gunnery	49	puszpang	f	84	0	0	0	\N	2026-07-29 20:35:07.316555	2026-07-29 20:35:07.316588	f	\N
25	Shunsen Port Battle Tank	defensive	64	puszpang	f	98	0	0	0	\N	2026-07-29 21:00:33.919052	2026-07-29 21:00:33.919083	f	\N
26	Shunsen Port Battle DPS	gunnery	64	puszpang	f	98	0	0	0	\N	2026-07-29 21:03:48.746647	2026-07-29 21:03:48.746671	f	\N
27	Polacca Port Battle Mortar	gunnery	62	puszpang	f	74	0	0	0	\N	2026-07-29 21:08:11.579331	2026-07-29 21:08:11.579354	f	\N
28	Golden Apostle Port Battle Barrel	gunnery	57	puszpang	f	96	0	0	0	\N	2026-07-29 21:10:43.732972	2026-07-29 21:10:43.732997	f	\N
2	Poltava - Open world PvP	gunnery	30	admin	f	119	0	0	0	Created by Puszpang - remade with the tool.	2026-07-24 18:00:02.776121	2026-07-24 18:14:14.976979	f	research_upgrade_slot
29	Ingermanland Open World PVP	gunnery	12	puszpang	f	137	0	0	0	\N	2026-07-29 21:35:54.747631	2026-07-29 21:35:54.747655	f	research_upgrade_slot
\.

CREATE TEMP TABLE _rbf_build_slot_stage (
    old_build_id integer NOT NULL,
    slot_type varchar(40) NOT NULL,
    slot_index integer NOT NULL,
    source_option_id integer NOT NULL,
    quantity integer,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    PRIMARY KEY (old_build_id, slot_type, slot_index)
) ON COMMIT DROP;

COPY _rbf_build_slot_stage (
    old_build_id, slot_type, slot_index, source_option_id,
    quantity, created_at, updated_at
) FROM stdin;
2	sail	1	3	\N	2026-07-24 18:14:14.981548	2026-07-24 18:14:14.98157
2	lantern	1	50	\N	2026-07-24 18:14:14.981577	2026-07-24 18:14:14.981583
2	upgrade	1	37	\N	2026-07-24 18:14:14.981589	2026-07-24 18:14:14.981594
2	upgrade	2	33	\N	2026-07-24 18:14:14.9816	2026-07-24 18:14:14.981605
2	upgrade	3	14	\N	2026-07-24 18:14:14.981611	2026-07-24 18:14:14.981617
2	upgrade	4	26	\N	2026-07-24 18:14:14.981623	2026-07-24 18:14:14.981628
2	upgrade	5	20	\N	2026-07-24 18:14:14.981634	2026-07-24 18:14:14.981639
2	upgrade	6	11	\N	2026-07-24 18:14:14.981645	2026-07-24 18:14:14.98165
2	upgrade	7	22	\N	2026-07-24 18:14:14.981656	2026-07-24 18:14:14.981661
2	weapon_front	1	173	4	2026-07-24 18:14:14.981667	2026-07-24 18:14:14.981672
2	weapon_port	1	145	23	2026-07-24 18:14:14.981678	2026-07-24 18:14:14.981684
2	weapon_starboard	1	145	23	2026-07-24 18:14:14.981689	2026-07-24 18:14:14.981694
2	special_crew	1	192	1	2026-07-24 18:14:14.9817	2026-07-24 18:14:14.981705
2	special_crew	2	189	1	2026-07-24 18:14:14.981711	2026-07-24 18:14:14.981716
2	special_crew	3	207	1	2026-07-24 18:14:14.981721	2026-07-24 18:14:14.981726
2	special_crew	4	178	1	2026-07-24 18:14:14.981731	2026-07-24 18:14:14.981736
2	ammunition	1	59	1	2026-07-24 18:14:14.981742	2026-07-24 18:14:14.981747
2	ammunition	2	55	1	2026-07-24 18:14:14.981752	2026-07-24 18:14:14.981757
2	ammunition	3	58	1	2026-07-24 18:14:14.981762	2026-07-24 18:14:14.981767
2	ammunition	4	56	1	2026-07-24 18:14:14.981772	2026-07-24 18:14:14.981777
2	consumable	1	77	1	2026-07-24 18:14:14.981783	2026-07-24 18:14:14.981788
2	consumable	2	68	1	2026-07-24 18:14:14.981793	2026-07-24 18:14:14.981799
2	consumable	3	75	1	2026-07-24 18:14:14.981804	2026-07-24 18:14:14.981809
5	sail	1	3	\N	2026-07-28 08:51:58.990512	2026-07-28 08:51:58.990534
5	lantern	1	48	\N	2026-07-28 08:51:58.990541	2026-07-28 08:51:58.990547
5	upgrade	1	40	\N	2026-07-28 08:51:58.990552	2026-07-28 08:51:58.990557
5	upgrade	2	11	\N	2026-07-28 08:51:58.990563	2026-07-28 08:51:58.990568
5	upgrade	3	10	\N	2026-07-28 08:51:58.990573	2026-07-28 08:51:58.990578
5	upgrade	4	19	\N	2026-07-28 08:51:58.990583	2026-07-28 08:51:58.990588
5	weapon_front	1	166	4	2026-07-28 08:51:58.990594	2026-07-28 08:51:58.990599
5	weapon_rear	1	169	4	2026-07-28 08:51:58.990604	2026-07-28 08:51:58.990609
5	weapon_port	1	148	42	2026-07-28 08:51:58.990614	2026-07-28 08:51:58.990619
5	weapon_starboard	1	148	42	2026-07-28 08:51:58.990625	2026-07-28 08:51:58.990631
5	special_crew	1	189	1	2026-07-28 08:51:58.990636	2026-07-28 08:51:58.990641
5	special_crew	2	222	1	2026-07-28 08:51:58.990647	2026-07-28 08:51:58.990652
5	special_crew	3	186	1	2026-07-28 08:51:58.990657	2026-07-28 08:51:58.990663
5	special_crew	4	187	1	2026-07-28 08:51:58.990669	2026-07-28 08:51:58.990674
5	ammunition	1	59	1500	2026-07-28 08:51:58.99068	2026-07-28 08:51:58.990685
5	ammunition	2	55	1500	2026-07-28 08:51:58.99069	2026-07-28 08:51:58.990695
5	ammunition	3	51	500	2026-07-28 08:51:58.990701	2026-07-28 08:51:58.990706
5	ammunition	4	54	500	2026-07-28 08:51:58.990711	2026-07-28 08:51:58.990716
5	ammunition	5	52	60	2026-07-28 08:51:58.990721	2026-07-28 08:51:58.990726
5	ammunition	6	58	5	2026-07-28 08:51:58.990732	2026-07-28 08:51:58.990737
5	ammunition	7	62	2	2026-07-28 08:51:58.990743	2026-07-28 08:51:58.990748
5	ammunition	8	61	5	2026-07-28 08:51:58.990753	2026-07-28 08:51:58.990758
5	ammunition	9	63	3	2026-07-28 08:51:58.990764	2026-07-28 08:51:58.990769
5	consumable	1	71	1	2026-07-28 08:51:58.990774	2026-07-28 08:51:58.990779
5	consumable	2	82	1	2026-07-28 08:51:58.990785	2026-07-28 08:51:58.99079
5	consumable	3	68	1	2026-07-28 08:51:58.990795	2026-07-28 08:51:58.9908
5	hold	1	134	500	2026-07-28 08:51:58.990806	2026-07-28 08:51:58.990811
5	hold	2	105	250	2026-07-28 08:51:58.990816	2026-07-28 08:51:58.990821
5	hold	3	107	200	2026-07-28 08:51:58.990827	2026-07-28 08:51:58.990832
6	sail	1	3	\N	2026-07-29 12:39:19.087522	2026-07-29 12:39:19.087541
6	lantern	1	45	\N	2026-07-29 12:39:19.087548	2026-07-29 12:39:19.087553
6	upgrade	1	15	\N	2026-07-29 12:39:19.087559	2026-07-29 12:39:19.087564
6	upgrade	2	23	\N	2026-07-29 12:39:19.08757	2026-07-29 12:39:19.087575
6	upgrade	3	38	\N	2026-07-29 12:39:19.087581	2026-07-29 12:39:19.087586
6	upgrade	4	36	\N	2026-07-29 12:39:19.087592	2026-07-29 12:39:19.087597
4	sail	1	3	\N	2026-07-26 20:38:29.079833	2026-07-26 20:38:29.079856
4	lantern	1	44	\N	2026-07-26 20:38:29.079863	2026-07-26 20:38:29.079868
4	upgrade	1	26	\N	2026-07-26 20:38:29.079874	2026-07-26 20:38:29.07988
4	upgrade	2	33	\N	2026-07-26 20:38:29.079885	2026-07-26 20:38:29.07989
4	upgrade	3	30	\N	2026-07-26 20:38:29.079895	2026-07-26 20:38:29.0799
4	upgrade	4	34	\N	2026-07-26 20:38:29.079906	2026-07-26 20:38:29.079911
4	weapon_port	1	147	16	2026-07-26 20:38:29.079916	2026-07-26 20:38:29.079921
4	weapon_starboard	1	147	16	2026-07-26 20:38:29.079926	2026-07-26 20:38:29.079931
4	special_crew	1	207	1	2026-07-26 20:38:29.079937	2026-07-26 20:38:29.079942
4	special_crew	2	224	1	2026-07-26 20:38:29.079947	2026-07-26 20:38:29.079952
4	special_crew	3	198	1	2026-07-26 20:38:29.079957	2026-07-26 20:38:29.079962
4	ammunition	1	51	300	2026-07-26 20:38:29.079967	2026-07-26 20:38:29.079972
4	ammunition	2	59	200	2026-07-26 20:38:29.079977	2026-07-26 20:38:29.079982
4	ammunition	3	58	5	2026-07-26 20:38:29.079988	2026-07-26 20:38:29.079993
4	consumable	1	66	100	2026-07-26 20:38:29.079998	2026-07-26 20:38:29.080003
4	consumable	2	69	100	2026-07-26 20:38:29.080009	2026-07-26 20:38:29.080014
4	consumable	3	75	100	2026-07-26 20:38:29.080019	2026-07-26 20:38:29.080024
6	upgrade	5	40	\N	2026-07-29 12:39:19.087603	2026-07-29 12:39:19.087608
6	weapon_front	1	168	2	2026-07-29 12:39:19.087613	2026-07-29 12:39:19.087619
6	weapon_port	1	152	1	2026-07-29 12:39:19.087625	2026-07-29 12:39:19.08763
6	weapon_port	2	149	1	2026-07-29 12:39:19.087635	2026-07-29 12:39:19.087641
6	weapon_starboard	1	152	1	2026-07-29 12:39:19.087646	2026-07-29 12:39:19.087652
6	weapon_starboard	2	149	1	2026-07-29 12:39:19.087657	2026-07-29 12:39:19.087662
6	special_crew	1	225	1	2026-07-29 12:39:19.087668	2026-07-29 12:39:19.087673
6	special_crew	2	219	1	2026-07-29 12:39:19.087679	2026-07-29 12:39:19.087684
6	special_crew	3	216	1	2026-07-29 12:39:19.08769	2026-07-29 12:39:19.087695
6	special_crew	4	222	1	2026-07-29 12:39:19.087701	2026-07-29 12:39:19.087706
6	ammunition	1	229	6000	2026-07-29 12:39:19.087711	2026-07-29 12:39:19.087717
6	consumable	1	76	1	2026-07-29 12:39:19.087723	2026-07-29 12:39:19.087728
6	consumable	2	86	1	2026-07-29 12:39:19.087733	2026-07-29 12:39:19.087739
6	consumable	3	68	1	2026-07-29 12:39:19.087744	2026-07-29 12:39:19.087749
6	hold	1	134	3000	2026-07-29 12:39:19.087755	2026-07-29 12:39:19.08776
6	hold	2	127	1000	2026-07-29 12:39:19.087766	2026-07-29 12:39:19.087771
6	hold	3	105	500	2026-07-29 12:39:19.087777	2026-07-29 12:39:19.087783
7	sail	1	3	\N	2026-07-29 18:34:02.336396	2026-07-29 18:34:02.336418
7	lantern	1	48	\N	2026-07-29 18:34:02.336425	2026-07-29 18:34:02.336431
7	upgrade	1	20	\N	2026-07-29 18:34:02.336438	2026-07-29 18:34:02.336444
7	upgrade	2	22	\N	2026-07-29 18:34:02.33645	2026-07-29 18:34:02.336455
7	upgrade	3	11	\N	2026-07-29 18:34:02.336461	2026-07-29 18:34:02.336466
7	upgrade	4	37	\N	2026-07-29 18:34:02.336471	2026-07-29 18:34:02.336477
7	upgrade	5	40	\N	2026-07-29 18:34:02.336482	2026-07-29 18:34:02.336487
7	upgrade	6	36	\N	2026-07-29 18:34:02.336493	2026-07-29 18:34:02.336498
7	weapon_port	1	152	1	2026-07-29 18:34:02.336504	2026-07-29 18:34:02.336509
7	weapon_port	2	149	1	2026-07-29 18:34:02.336515	2026-07-29 18:34:02.33652
7	weapon_starboard	1	152	1	2026-07-29 18:34:02.336525	2026-07-29 18:34:02.336531
7	weapon_starboard	2	149	1	2026-07-29 18:34:02.336537	2026-07-29 18:34:02.336542
7	special_crew	1	222	1	2026-07-29 18:34:02.336547	2026-07-29 18:34:02.336552
7	special_crew	2	216	1	2026-07-29 18:34:02.336558	2026-07-29 18:34:02.336563
7	special_crew	3	192	1	2026-07-29 18:34:02.336568	2026-07-29 18:34:02.336574
7	special_crew	4	219	1	2026-07-29 18:34:02.33658	2026-07-29 18:34:02.336585
7	ammunition	1	229	6000	2026-07-29 18:34:02.33659	2026-07-29 18:34:02.336595
7	consumable	1	77	1	2026-07-29 18:34:02.336601	2026-07-29 18:34:02.336606
7	consumable	2	86	1	2026-07-29 18:34:02.336612	2026-07-29 18:34:02.336617
7	consumable	3	68	1	2026-07-29 18:34:02.336622	2026-07-29 18:34:02.336627
7	hold	1	134	3000	2026-07-29 18:34:02.336633	2026-07-29 18:34:02.336638
7	hold	2	105	500	2026-07-29 18:34:02.336643	2026-07-29 18:34:02.336648
7	hold	3	127	1000	2026-07-29 18:34:02.336654	2026-07-29 18:34:02.336659
8	sail	1	3	\N	2026-07-29 18:42:48.531611	2026-07-29 18:42:48.531633
8	lantern	1	48	\N	2026-07-29 18:42:48.53164	2026-07-29 18:42:48.531646
8	upgrade	1	27	\N	2026-07-29 18:42:48.531652	2026-07-29 18:42:48.531658
8	upgrade	2	39	\N	2026-07-29 18:42:48.531663	2026-07-29 18:42:48.531668
8	upgrade	3	34	\N	2026-07-29 18:42:48.531674	2026-07-29 18:42:48.531679
8	upgrade	4	37	\N	2026-07-29 18:42:48.531684	2026-07-29 18:42:48.531689
8	upgrade	5	38	\N	2026-07-29 18:42:48.531695	2026-07-29 18:42:48.5317
8	upgrade	6	36	\N	2026-07-29 18:42:48.531705	2026-07-29 18:42:48.531711
8	weapon_front	1	177	6	2026-07-29 18:42:48.531716	2026-07-29 18:42:48.531721
8	weapon_port	1	152	1	2026-07-29 18:42:48.531727	2026-07-29 18:42:48.531732
8	weapon_port	2	149	1	2026-07-29 18:42:48.531737	2026-07-29 18:42:48.531742
8	weapon_starboard	1	152	1	2026-07-29 18:42:48.531747	2026-07-29 18:42:48.531752
8	weapon_starboard	2	149	1	2026-07-29 18:42:48.531758	2026-07-29 18:42:48.531763
8	weapon_mortar	1	137	3	2026-07-29 18:42:48.531769	2026-07-29 18:42:48.531774
8	special_crew	1	179	1	2026-07-29 18:42:48.531779	2026-07-29 18:42:48.531784
8	special_crew	2	220	1	2026-07-29 18:42:48.531789	2026-07-29 18:42:48.531794
8	special_crew	3	222	1	2026-07-29 18:42:48.531799	2026-07-29 18:42:48.531804
8	special_crew	4	216	1	2026-07-29 18:42:48.53181	2026-07-29 18:42:48.531815
8	ammunition	1	229	6000	2026-07-29 18:42:48.53182	2026-07-29 18:42:48.531825
8	ammunition	2	64	160	2026-07-29 18:42:48.53183	2026-07-29 18:42:48.531835
8	consumable	1	87	1	2026-07-29 18:42:48.53184	2026-07-29 18:42:48.531845
8	consumable	2	86	1	2026-07-29 18:42:48.53185	2026-07-29 18:42:48.531855
8	consumable	3	68	1	2026-07-29 18:42:48.53186	2026-07-29 18:42:48.531865
8	hold	1	134	3000	2026-07-29 18:42:48.531871	2026-07-29 18:42:48.531876
8	hold	2	127	1000	2026-07-29 18:42:48.531881	2026-07-29 18:42:48.531886
8	hold	3	105	500	2026-07-29 18:42:48.531892	2026-07-29 18:42:48.531897
9	sail	1	3	\N	2026-07-29 18:48:47.828327	2026-07-29 18:48:47.828349
9	lantern	1	48	\N	2026-07-29 18:48:47.828356	2026-07-29 18:48:47.828361
9	upgrade	1	25	\N	2026-07-29 18:48:47.828367	2026-07-29 18:48:47.828372
9	upgrade	2	37	\N	2026-07-29 18:48:47.828378	2026-07-29 18:48:47.828383
9	upgrade	3	27	\N	2026-07-29 18:48:47.828389	2026-07-29 18:48:47.828394
9	upgrade	4	36	\N	2026-07-29 18:48:47.828399	2026-07-29 18:48:47.828404
9	upgrade	5	38	\N	2026-07-29 18:48:47.82841	2026-07-29 18:48:47.828415
9	upgrade	6	34	\N	2026-07-29 18:48:47.82842	2026-07-29 18:48:47.828425
9	weapon_front	1	177	8	2026-07-29 18:48:47.82843	2026-07-29 18:48:47.828435
9	weapon_rear	1	177	4	2026-07-29 18:48:47.828441	2026-07-29 18:48:47.828447
9	weapon_port	1	152	1	2026-07-29 18:48:47.828452	2026-07-29 18:48:47.828458
9	weapon_port	2	149	1	2026-07-29 18:48:47.828464	2026-07-29 18:48:47.828469
9	weapon_starboard	1	152	1	2026-07-29 18:48:47.828475	2026-07-29 18:48:47.82848
9	weapon_starboard	2	149	1	2026-07-29 18:48:47.828486	2026-07-29 18:48:47.828491
9	weapon_mortar	1	164	2	2026-07-29 18:48:47.828496	2026-07-29 18:48:47.828501
9	special_crew	1	179	1	2026-07-29 18:48:47.828506	2026-07-29 18:48:47.828511
9	special_crew	2	220	1	2026-07-29 18:48:47.828517	2026-07-29 18:48:47.828523
9	special_crew	3	216	1	2026-07-29 18:48:47.828528	2026-07-29 18:48:47.828533
9	special_crew	4	222	1	2026-07-29 18:48:47.828539	2026-07-29 18:48:47.828544
9	ammunition	1	229	6000	2026-07-29 18:48:47.828549	2026-07-29 18:48:47.828554
9	ammunition	2	61	30	2026-07-29 18:48:47.82856	2026-07-29 18:48:47.828564
9	consumable	1	87	1	2026-07-29 18:48:47.82857	2026-07-29 18:48:47.828575
9	consumable	2	86	1	2026-07-29 18:48:47.828581	2026-07-29 18:48:47.828586
9	consumable	3	68	1	2026-07-29 18:48:47.828591	2026-07-29 18:48:47.828596
9	hold	1	134	3000	2026-07-29 18:48:47.828602	2026-07-29 18:48:47.828607
9	hold	2	127	1000	2026-07-29 18:48:47.828612	2026-07-29 18:48:47.828617
9	hold	3	105	500	2026-07-29 18:48:47.828622	2026-07-29 18:48:47.828627
10	sail	1	3	\N	2026-07-29 18:58:46.461796	2026-07-29 18:58:46.461819
10	lantern	1	44	\N	2026-07-29 18:58:46.461826	2026-07-29 18:58:46.461831
10	upgrade	1	15	\N	2026-07-29 18:58:46.461837	2026-07-29 18:58:46.461843
10	upgrade	2	23	\N	2026-07-29 18:58:46.461848	2026-07-29 18:58:46.461853
10	upgrade	3	37	\N	2026-07-29 18:58:46.461858	2026-07-29 18:58:46.461863
10	upgrade	4	38	\N	2026-07-29 18:58:46.461869	2026-07-29 18:58:46.461874
10	upgrade	5	40	\N	2026-07-29 18:58:46.461879	2026-07-29 18:58:46.461884
10	upgrade	6	36	\N	2026-07-29 18:58:46.461889	2026-07-29 18:58:46.461894
10	weapon_port	1	152	1	2026-07-29 18:58:46.461899	2026-07-29 18:58:46.461904
10	weapon_port	2	149	1	2026-07-29 18:58:46.46191	2026-07-29 18:58:46.461915
10	weapon_starboard	1	152	1	2026-07-29 18:58:46.46192	2026-07-29 18:58:46.461925
10	weapon_starboard	2	149	1	2026-07-29 18:58:46.46193	2026-07-29 18:58:46.461935
10	special_crew	1	225	1	2026-07-29 18:58:46.461941	2026-07-29 18:58:46.461946
10	special_crew	2	219	1	2026-07-29 18:58:46.461951	2026-07-29 18:58:46.461957
10	special_crew	3	222	1	2026-07-29 18:58:46.461963	2026-07-29 18:58:46.461968
10	special_crew	4	216	1	2026-07-29 18:58:46.461973	2026-07-29 18:58:46.461978
10	ammunition	1	229	5000	2026-07-29 18:58:46.461984	2026-07-29 18:58:46.461989
10	consumable	1	76	1	2026-07-29 18:58:46.461995	2026-07-29 18:58:46.462
10	consumable	2	86	1	2026-07-29 18:58:46.462006	2026-07-29 18:58:46.462011
10	consumable	3	68	1	2026-07-29 18:58:46.462017	2026-07-29 18:58:46.462022
10	hold	1	134	3000	2026-07-29 18:58:46.462027	2026-07-29 18:58:46.462032
10	hold	2	127	1000	2026-07-29 18:58:46.462038	2026-07-29 18:58:46.462043
10	hold	3	105	500	2026-07-29 18:58:46.462048	2026-07-29 18:58:46.462053
11	sail	1	3	\N	2026-07-29 19:03:08.427053	2026-07-29 19:03:08.427076
11	lantern	1	44	\N	2026-07-29 19:03:08.427083	2026-07-29 19:03:08.427088
11	upgrade	1	20	\N	2026-07-29 19:03:08.427094	2026-07-29 19:03:08.427099
11	upgrade	2	22	\N	2026-07-29 19:03:08.427105	2026-07-29 19:03:08.42711
11	upgrade	3	37	\N	2026-07-29 19:03:08.427116	2026-07-29 19:03:08.427121
11	upgrade	4	36	\N	2026-07-29 19:03:08.427126	2026-07-29 19:03:08.427131
11	upgrade	5	11	\N	2026-07-29 19:03:08.427137	2026-07-29 19:03:08.427143
11	upgrade	6	40	\N	2026-07-29 19:03:08.427148	2026-07-29 19:03:08.427154
11	weapon_port	1	152	1	2026-07-29 19:03:08.427159	2026-07-29 19:03:08.427165
11	weapon_port	2	149	1	2026-07-29 19:03:08.42717	2026-07-29 19:03:08.427175
11	weapon_starboard	1	152	1	2026-07-29 19:03:08.427181	2026-07-29 19:03:08.427186
11	weapon_starboard	2	149	1	2026-07-29 19:03:08.427191	2026-07-29 19:03:08.427197
11	special_crew	1	219	1	2026-07-29 19:03:08.427203	2026-07-29 19:03:08.427208
11	special_crew	2	216	1	2026-07-29 19:03:08.427214	2026-07-29 19:03:08.427219
11	special_crew	3	192	1	2026-07-29 19:03:08.427224	2026-07-29 19:03:08.427229
11	special_crew	4	222	1	2026-07-29 19:03:08.427235	2026-07-29 19:03:08.42724
11	ammunition	1	229	5000	2026-07-29 19:03:08.427245	2026-07-29 19:03:08.42725
11	consumable	1	86	1	2026-07-29 19:03:08.427256	2026-07-29 19:03:08.427261
11	consumable	2	77	1	2026-07-29 19:03:08.427266	2026-07-29 19:03:08.427271
11	consumable	3	68	1	2026-07-29 19:03:08.427277	2026-07-29 19:03:08.427282
11	hold	1	134	3000	2026-07-29 19:03:08.427287	2026-07-29 19:03:08.427292
11	hold	2	105	500	2026-07-29 19:03:08.427298	2026-07-29 19:03:08.427303
11	hold	3	127	1000	2026-07-29 19:03:08.427308	2026-07-29 19:03:08.427313
12	sail	1	3	\N	2026-07-29 19:09:13.582666	2026-07-29 19:09:13.582688
12	lantern	1	48	\N	2026-07-29 19:09:13.582694	2026-07-29 19:09:13.5827
12	upgrade	1	37	\N	2026-07-29 19:09:13.582706	2026-07-29 19:09:13.582711
12	upgrade	2	27	\N	2026-07-29 19:09:13.582717	2026-07-29 19:09:13.582722
12	upgrade	3	39	\N	2026-07-29 19:09:13.582727	2026-07-29 19:09:13.582732
12	upgrade	4	34	\N	2026-07-29 19:09:13.582738	2026-07-29 19:09:13.582744
12	upgrade	5	38	\N	2026-07-29 19:09:13.582749	2026-07-29 19:09:13.582754
12	upgrade	6	36	\N	2026-07-29 19:09:13.58276	2026-07-29 19:09:13.582765
12	weapon_front	1	168	1	2026-07-29 19:09:13.582771	2026-07-29 19:09:13.582777
12	weapon_port	1	145	22	2026-07-29 19:09:13.582783	2026-07-29 19:09:13.582788
12	weapon_starboard	1	145	22	2026-07-29 19:09:13.582793	2026-07-29 19:09:13.582798
12	weapon_mortar	1	137	2	2026-07-29 19:09:13.582804	2026-07-29 19:09:13.582809
12	special_crew	1	179	1	2026-07-29 19:09:13.582814	2026-07-29 19:09:13.582819
12	special_crew	2	220	1	2026-07-29 19:09:13.582825	2026-07-29 19:09:13.58283
12	special_crew	3	222	1	2026-07-29 19:09:13.582835	2026-07-29 19:09:13.58284
12	special_crew	4	216	1	2026-07-29 19:09:13.582846	2026-07-29 19:09:13.582851
12	ammunition	1	229	5000	2026-07-29 19:09:13.582856	2026-07-29 19:09:13.582862
12	ammunition	2	64	150	2026-07-29 19:09:13.582867	2026-07-29 19:09:13.582872
12	consumable	1	87	1	2026-07-29 19:09:13.582878	2026-07-29 19:09:13.582883
12	consumable	2	86	1	2026-07-29 19:09:13.582889	2026-07-29 19:09:13.582894
12	consumable	3	68	1	2026-07-29 19:09:13.582899	2026-07-29 19:09:13.582904
12	hold	1	134	3000	2026-07-29 19:09:13.582909	2026-07-29 19:09:13.582915
12	hold	2	127	1000	2026-07-29 19:09:13.58292	2026-07-29 19:09:13.582925
12	hold	3	105	500	2026-07-29 19:09:13.58293	2026-07-29 19:09:13.582936
13	sail	1	3	\N	2026-07-29 19:15:46.810983	2026-07-29 19:15:46.811013
13	lantern	1	48	\N	2026-07-29 19:15:46.811025	2026-07-29 19:15:46.811035
13	upgrade	1	25	\N	2026-07-29 19:15:46.811045	2026-07-29 19:15:46.811055
13	upgrade	2	27	\N	2026-07-29 19:15:46.811065	2026-07-29 19:15:46.811074
13	upgrade	3	37	\N	2026-07-29 19:15:46.811085	2026-07-29 19:15:46.811094
13	upgrade	4	38	\N	2026-07-29 19:15:46.811104	2026-07-29 19:15:46.811112
13	upgrade	5	36	\N	2026-07-29 19:15:46.811122	2026-07-29 19:15:46.811131
13	upgrade	6	34	\N	2026-07-29 19:15:46.811141	2026-07-29 19:15:46.81115
13	weapon_rear	1	177	4	2026-07-29 19:15:46.81116	2026-07-29 19:15:46.811169
13	weapon_port	1	152	1	2026-07-29 19:15:46.811178	2026-07-29 19:15:46.811187
13	weapon_port	2	149	1	2026-07-29 19:15:46.811197	2026-07-29 19:15:46.811206
13	weapon_starboard	1	152	1	2026-07-29 19:15:46.811216	2026-07-29 19:15:46.811225
13	weapon_starboard	2	149	1	2026-07-29 19:15:46.811235	2026-07-29 19:15:46.811244
13	weapon_mortar	1	164	2	2026-07-29 19:15:46.811253	2026-07-29 19:15:46.811263
13	special_crew	1	179	1	2026-07-29 19:15:46.811273	2026-07-29 19:15:46.811282
13	special_crew	2	220	1	2026-07-29 19:15:46.811291	2026-07-29 19:15:46.8113
13	special_crew	3	222	1	2026-07-29 19:15:46.81131	2026-07-29 19:15:46.81132
13	special_crew	4	216	1	2026-07-29 19:15:46.811331	2026-07-29 19:15:46.81134
13	ammunition	1	229	5000	2026-07-29 19:15:46.81135	2026-07-29 19:15:46.811359
13	ammunition	2	61	50	2026-07-29 19:15:46.811369	2026-07-29 19:15:46.811378
13	consumable	1	87	1	2026-07-29 19:15:46.811388	2026-07-29 19:15:46.811398
13	consumable	2	86	1	2026-07-29 19:15:46.811409	2026-07-29 19:15:46.811418
13	consumable	3	68	1	2026-07-29 19:15:46.811428	2026-07-29 19:15:46.811437
13	hold	1	134	3000	2026-07-29 19:15:46.811447	2026-07-29 19:15:46.811457
13	hold	2	127	1000	2026-07-29 19:15:46.811467	2026-07-29 19:15:46.811476
13	hold	3	105	500	2026-07-29 19:15:46.811485	2026-07-29 19:15:46.811495
14	sail	1	3	\N	2026-07-29 19:26:23.316246	2026-07-29 19:26:23.316269
14	lantern	1	44	\N	2026-07-29 19:26:23.316275	2026-07-29 19:26:23.31628
14	upgrade	1	15	\N	2026-07-29 19:26:23.316286	2026-07-29 19:26:23.316291
14	upgrade	2	23	\N	2026-07-29 19:26:23.316297	2026-07-29 19:26:23.316302
14	upgrade	3	37	\N	2026-07-29 19:26:23.316307	2026-07-29 19:26:23.316312
14	upgrade	4	38	\N	2026-07-29 19:26:23.316318	2026-07-29 19:26:23.316322
14	upgrade	5	40	\N	2026-07-29 19:26:23.316328	2026-07-29 19:26:23.316333
14	upgrade	6	36	\N	2026-07-29 19:26:23.316338	2026-07-29 19:26:23.316345
14	weapon_front	1	168	1	2026-07-29 19:26:23.316351	2026-07-29 19:26:23.316356
14	weapon_port	1	145	25	2026-07-29 19:26:23.316362	2026-07-29 19:26:23.316367
14	weapon_starboard	1	145	25	2026-07-29 19:26:23.316373	2026-07-29 19:26:23.316378
14	special_crew	1	222	1	2026-07-29 19:26:23.316383	2026-07-29 19:26:23.316388
14	special_crew	2	225	1	2026-07-29 19:26:23.316394	2026-07-29 19:26:23.316399
14	special_crew	3	219	1	2026-07-29 19:26:23.316404	2026-07-29 19:26:23.316409
14	special_crew	4	216	1	2026-07-29 19:26:23.316415	2026-07-29 19:26:23.31642
14	ammunition	1	229	4000	2026-07-29 19:26:23.316425	2026-07-29 19:26:23.31643
14	consumable	1	68	1	2026-07-29 19:26:23.316436	2026-07-29 19:26:23.316441
14	consumable	2	86	1	2026-07-29 19:26:23.316446	2026-07-29 19:26:23.316451
14	consumable	3	76	1	2026-07-29 19:26:23.316456	2026-07-29 19:26:23.316462
14	hold	1	134	3000	2026-07-29 19:26:23.316468	2026-07-29 19:26:23.316473
14	hold	2	105	500	2026-07-29 19:26:23.316478	2026-07-29 19:26:23.316484
14	hold	3	127	1000	2026-07-29 19:26:23.316489	2026-07-29 19:26:23.316494
15	sail	1	3	\N	2026-07-29 19:32:05.809867	2026-07-29 19:32:05.809891
15	lantern	1	44	\N	2026-07-29 19:32:05.809898	2026-07-29 19:32:05.809904
15	upgrade	1	20	\N	2026-07-29 19:32:05.80991	2026-07-29 19:32:05.809916
15	upgrade	2	22	\N	2026-07-29 19:32:05.809922	2026-07-29 19:32:05.809928
15	upgrade	3	37	\N	2026-07-29 19:32:05.809933	2026-07-29 19:32:05.809939
15	upgrade	4	11	\N	2026-07-29 19:32:05.809945	2026-07-29 19:32:05.80995
15	upgrade	5	36	\N	2026-07-29 19:32:05.809956	2026-07-29 19:32:05.809961
15	upgrade	6	40	\N	2026-07-29 19:32:05.809967	2026-07-29 19:32:05.809972
15	weapon_port	1	145	35	2026-07-29 19:32:05.809977	2026-07-29 19:32:05.809983
15	weapon_starboard	1	145	35	2026-07-29 19:32:05.809989	2026-07-29 19:32:05.809995
15	special_crew	1	222	1	2026-07-29 19:32:05.81	2026-07-29 19:32:05.810005
15	special_crew	2	216	1	2026-07-29 19:32:05.810011	2026-07-29 19:32:05.810016
15	special_crew	3	219	1	2026-07-29 19:32:05.810021	2026-07-29 19:32:05.810026
15	special_crew	4	192	1	2026-07-29 19:32:05.810032	2026-07-29 19:32:05.810037
15	ammunition	1	229	4000	2026-07-29 19:32:05.810042	2026-07-29 19:32:05.810047
15	consumable	1	68	1	2026-07-29 19:32:05.810053	2026-07-29 19:32:05.810058
15	consumable	2	86	1	2026-07-29 19:32:05.810064	2026-07-29 19:32:05.810069
15	consumable	3	77	1	2026-07-29 19:32:05.810075	2026-07-29 19:32:05.810079
15	hold	1	134	3000	2026-07-29 19:32:05.810085	2026-07-29 19:32:05.81009
15	hold	2	105	500	2026-07-29 19:32:05.810095	2026-07-29 19:32:05.8101
15	hold	3	127	1000	2026-07-29 19:32:05.810107	2026-07-29 19:32:05.810112
16	sail	1	3	\N	2026-07-29 19:39:03.709157	2026-07-29 19:39:03.709185
16	lantern	1	48	\N	2026-07-29 19:39:03.709195	2026-07-29 19:39:03.709204
16	upgrade	1	37	\N	2026-07-29 19:39:03.709213	2026-07-29 19:39:03.709221
16	upgrade	2	27	\N	2026-07-29 19:39:03.70923	2026-07-29 19:39:03.709238
16	upgrade	3	25	\N	2026-07-29 19:39:03.709247	2026-07-29 19:39:03.709255
16	upgrade	4	38	\N	2026-07-29 19:39:03.709264	2026-07-29 19:39:03.709271
16	upgrade	5	36	\N	2026-07-29 19:39:03.70928	2026-07-29 19:39:03.709287
16	upgrade	6	34	\N	2026-07-29 19:39:03.709296	2026-07-29 19:39:03.709303
16	weapon_port	1	145	15	2026-07-29 19:39:03.709312	2026-07-29 19:39:03.709319
16	weapon_starboard	1	145	15	2026-07-29 19:39:03.709328	2026-07-29 19:39:03.709337
16	weapon_mortar	1	164	4	2026-07-29 19:39:03.709345	2026-07-29 19:39:03.709354
16	special_crew	1	179	1	2026-07-29 19:39:03.709362	2026-07-29 19:39:03.70937
16	special_crew	2	220	1	2026-07-29 19:39:03.709379	2026-07-29 19:39:03.709386
16	special_crew	3	222	1	2026-07-29 19:39:03.709395	2026-07-29 19:39:03.709402
16	special_crew	4	216	1	2026-07-29 19:39:03.70941	2026-07-29 19:39:03.709418
16	ammunition	1	229	3000	2026-07-29 19:39:03.709426	2026-07-29 19:39:03.709434
16	ammunition	2	61	100	2026-07-29 19:39:03.709442	2026-07-29 19:39:03.70945
16	consumable	1	87	1	2026-07-29 19:39:03.709458	2026-07-29 19:39:03.709466
16	consumable	2	68	1	2026-07-29 19:39:03.709474	2026-07-29 19:39:03.709482
16	consumable	3	86	1	2026-07-29 19:39:03.70949	2026-07-29 19:39:03.709497
16	hold	1	134	3000	2026-07-29 19:39:03.709506	2026-07-29 19:39:03.709513
16	hold	2	105	500	2026-07-29 19:39:03.709521	2026-07-29 19:39:03.709529
16	hold	3	127	1000	2026-07-29 19:39:03.709537	2026-07-29 19:39:03.709545
17	sail	1	3	\N	2026-07-29 19:45:57.849163	2026-07-29 19:45:57.849194
17	lantern	1	44	\N	2026-07-29 19:45:57.849206	2026-07-29 19:45:57.849216
17	upgrade	1	37	\N	2026-07-29 19:45:57.849226	2026-07-29 19:45:57.849235
17	upgrade	2	15	\N	2026-07-29 19:45:57.849246	2026-07-29 19:45:57.849255
17	upgrade	3	23	\N	2026-07-29 19:45:57.849266	2026-07-29 19:45:57.849276
17	upgrade	4	38	\N	2026-07-29 19:45:57.849287	2026-07-29 19:45:57.849296
17	upgrade	5	36	\N	2026-07-29 19:45:57.849306	2026-07-29 19:45:57.849316
17	upgrade	6	40	\N	2026-07-29 19:45:57.849326	2026-07-29 19:45:57.849335
17	weapon_port	1	145	26	2026-07-29 19:45:57.849345	2026-07-29 19:45:57.849354
17	weapon_starboard	1	145	26	2026-07-29 19:45:57.849364	2026-07-29 19:45:57.849373
17	special_crew	1	225	1	2026-07-29 19:45:57.849384	2026-07-29 19:45:57.849393
17	special_crew	2	219	1	2026-07-29 19:45:57.849403	2026-07-29 19:45:57.849412
17	special_crew	3	216	1	2026-07-29 19:45:57.849422	2026-07-29 19:45:57.849431
17	special_crew	4	222	1	2026-07-29 19:45:57.849441	2026-07-29 19:45:57.84945
17	ammunition	1	229	3000	2026-07-29 19:45:57.849459	2026-07-29 19:45:57.849468
17	consumable	1	68	1	2026-07-29 19:45:57.849478	2026-07-29 19:45:57.849487
17	consumable	2	86	1	2026-07-29 19:45:57.849497	2026-07-29 19:45:57.849506
17	consumable	3	76	1	2026-07-29 19:45:57.849516	2026-07-29 19:45:57.849525
17	hold	1	134	3000	2026-07-29 19:45:57.849535	2026-07-29 19:45:57.849544
17	hold	2	105	500	2026-07-29 19:45:57.849554	2026-07-29 19:45:57.849563
17	hold	3	127	1000	2026-07-29 19:45:57.849573	2026-07-29 19:45:57.849582
18	sail	1	3	\N	2026-07-29 19:49:02.329322	2026-07-29 19:49:02.329352
18	lantern	1	44	\N	2026-07-29 19:49:02.329363	2026-07-29 19:49:02.329373
18	upgrade	1	37	\N	2026-07-29 19:49:02.329383	2026-07-29 19:49:02.329392
18	upgrade	2	20	\N	2026-07-29 19:49:02.329402	2026-07-29 19:49:02.329412
18	upgrade	3	22	\N	2026-07-29 19:49:02.329421	2026-07-29 19:49:02.32943
18	upgrade	4	11	\N	2026-07-29 19:49:02.32944	2026-07-29 19:49:02.329449
18	upgrade	5	40	\N	2026-07-29 19:49:02.329459	2026-07-29 19:49:02.329469
18	upgrade	6	36	\N	2026-07-29 19:49:02.329479	2026-07-29 19:49:02.329488
18	weapon_port	1	145	26	2026-07-29 19:49:02.329498	2026-07-29 19:49:02.329506
18	weapon_starboard	1	145	26	2026-07-29 19:49:02.329516	2026-07-29 19:49:02.329525
18	special_crew	1	222	1	2026-07-29 19:49:02.329535	2026-07-29 19:49:02.329544
18	special_crew	2	219	1	2026-07-29 19:49:02.329554	2026-07-29 19:49:02.329562
18	special_crew	3	216	1	2026-07-29 19:49:02.329572	2026-07-29 19:49:02.329581
18	special_crew	4	192	1	2026-07-29 19:49:02.329591	2026-07-29 19:49:02.329599
18	ammunition	1	229	3000	2026-07-29 19:49:02.329609	2026-07-29 19:49:02.329618
18	consumable	1	68	1	2026-07-29 19:49:02.329628	2026-07-29 19:49:02.329637
18	consumable	2	77	1	2026-07-29 19:49:02.329646	2026-07-29 19:49:02.329655
18	consumable	3	86	1	2026-07-29 19:49:02.329665	2026-07-29 19:49:02.329674
18	hold	1	134	3000	2026-07-29 19:49:02.329683	2026-07-29 19:49:02.329693
18	hold	2	127	1000	2026-07-29 19:49:02.329703	2026-07-29 19:49:02.329711
18	hold	3	105	500	2026-07-29 19:49:02.329721	2026-07-29 19:49:02.32973
19	sail	1	3	\N	2026-07-29 20:00:36.564676	2026-07-29 20:00:36.564702
19	lantern	1	48	\N	2026-07-29 20:00:36.564709	2026-07-29 20:00:36.564715
19	upgrade	1	37	\N	2026-07-29 20:00:36.56476	2026-07-29 20:00:36.564766
19	upgrade	2	27	\N	2026-07-29 20:00:36.564772	2026-07-29 20:00:36.564777
19	upgrade	3	39	\N	2026-07-29 20:00:36.564783	2026-07-29 20:00:36.564788
19	upgrade	4	38	\N	2026-07-29 20:00:36.564794	2026-07-29 20:00:36.564799
19	upgrade	5	34	\N	2026-07-29 20:00:36.564805	2026-07-29 20:00:36.564811
19	upgrade	6	36	\N	2026-07-29 20:00:36.564816	2026-07-29 20:00:36.564822
19	weapon_port	1	145	4	2026-07-29 20:00:36.564828	2026-07-29 20:00:36.564833
19	weapon_starboard	1	145	4	2026-07-29 20:00:36.564838	2026-07-29 20:00:36.564844
19	weapon_mortar	1	159	3	2026-07-29 20:00:36.56485	2026-07-29 20:00:36.564856
19	special_crew	1	179	1	2026-07-29 20:00:36.564862	2026-07-29 20:00:36.564867
19	special_crew	2	220	1	2026-07-29 20:00:36.564873	2026-07-29 20:00:36.564878
19	special_crew	3	222	1	2026-07-29 20:00:36.564884	2026-07-29 20:00:36.564889
19	special_crew	4	216	1	2026-07-29 20:00:36.564894	2026-07-29 20:00:36.564899
19	ammunition	1	229	2000	2026-07-29 20:00:36.564905	2026-07-29 20:00:36.56491
19	ammunition	2	64	300	2026-07-29 20:00:36.564916	2026-07-29 20:00:36.564921
19	consumable	1	87	1	2026-07-29 20:00:36.564926	2026-07-29 20:00:36.564931
19	consumable	2	68	1	2026-07-29 20:00:36.564937	2026-07-29 20:00:36.564942
19	consumable	3	86	1	2026-07-29 20:00:36.564948	2026-07-29 20:00:36.564953
19	hold	1	134	3000	2026-07-29 20:00:36.564959	2026-07-29 20:00:36.564964
19	hold	2	105	500	2026-07-29 20:00:36.56497	2026-07-29 20:00:36.564975
19	hold	3	127	1000	2026-07-29 20:00:36.564981	2026-07-29 20:00:36.564986
20	sail	1	3	\N	2026-07-29 20:05:49.995042	2026-07-29 20:05:49.995065
20	lantern	1	48	\N	2026-07-29 20:05:49.995072	2026-07-29 20:05:49.995077
20	upgrade	1	37	\N	2026-07-29 20:05:49.995083	2026-07-29 20:05:49.995089
20	upgrade	2	25	\N	2026-07-29 20:05:49.995094	2026-07-29 20:05:49.995099
20	upgrade	3	27	\N	2026-07-29 20:05:49.995105	2026-07-29 20:05:49.99511
20	upgrade	4	38	\N	2026-07-29 20:05:49.995115	2026-07-29 20:05:49.99512
20	upgrade	5	36	\N	2026-07-29 20:05:49.995125	2026-07-29 20:05:49.99513
20	upgrade	6	34	\N	2026-07-29 20:05:49.995136	2026-07-29 20:05:49.995141
20	weapon_port	1	145	15	2026-07-29 20:05:49.995146	2026-07-29 20:05:49.995151
20	weapon_starboard	1	145	15	2026-07-29 20:05:49.995157	2026-07-29 20:05:49.995162
20	weapon_mortar	1	164	1	2026-07-29 20:05:49.995167	2026-07-29 20:05:49.995172
20	special_crew	1	179	1	2026-07-29 20:05:49.995178	2026-07-29 20:05:49.995183
20	special_crew	2	220	1	2026-07-29 20:05:49.995189	2026-07-29 20:05:49.995194
20	special_crew	3	216	1	2026-07-29 20:05:49.995199	2026-07-29 20:05:49.995205
20	special_crew	4	222	1	2026-07-29 20:05:49.99521	2026-07-29 20:05:49.995215
20	ammunition	1	229	2000	2026-07-29 20:05:49.99522	2026-07-29 20:05:49.995225
20	ammunition	2	61	100	2026-07-29 20:05:49.99523	2026-07-29 20:05:49.995235
20	consumable	1	68	1	2026-07-29 20:05:49.995241	2026-07-29 20:05:49.995246
20	consumable	2	86	1	2026-07-29 20:05:49.995251	2026-07-29 20:05:49.995256
20	consumable	3	87	1	2026-07-29 20:05:49.995261	2026-07-29 20:05:49.995266
20	hold	1	134	2000	2026-07-29 20:05:49.995271	2026-07-29 20:05:49.995276
20	hold	2	105	300	2026-07-29 20:05:49.995282	2026-07-29 20:05:49.995287
20	hold	3	127	600	2026-07-29 20:05:49.995292	2026-07-29 20:05:49.995297
21	sail	1	3	\N	2026-07-29 20:13:27.600754	2026-07-29 20:13:27.60078
21	lantern	1	48	\N	2026-07-29 20:13:27.600787	2026-07-29 20:13:27.600792
21	upgrade	1	37	\N	2026-07-29 20:13:27.600798	2026-07-29 20:13:27.600803
21	upgrade	2	15	\N	2026-07-29 20:13:27.600809	2026-07-29 20:13:27.600814
21	upgrade	3	23	\N	2026-07-29 20:13:27.600819	2026-07-29 20:13:27.600824
21	upgrade	4	38	\N	2026-07-29 20:13:27.60083	2026-07-29 20:13:27.600835
21	upgrade	5	36	\N	2026-07-29 20:13:27.60084	2026-07-29 20:13:27.600845
21	upgrade	6	40	\N	2026-07-29 20:13:27.600851	2026-07-29 20:13:27.600856
21	weapon_port	1	161	20	2026-07-29 20:13:27.600861	2026-07-29 20:13:27.600866
21	weapon_starboard	1	161	20	2026-07-29 20:13:27.600872	2026-07-29 20:13:27.600877
22	sail	1	3	\N	2026-07-29 20:16:46.10521	2026-07-29 20:16:46.105233
21	special_crew	1	225	1	2026-07-29 20:13:27.600882	2026-07-29 20:13:27.600887
21	special_crew	2	219	1	2026-07-29 20:13:27.600892	2026-07-29 20:13:27.600897
21	special_crew	3	222	1	2026-07-29 20:13:27.600903	2026-07-29 20:13:27.600908
21	special_crew	4	216	1	2026-07-29 20:13:27.600913	2026-07-29 20:13:27.600918
21	ammunition	1	229	2000	2026-07-29 20:13:27.600924	2026-07-29 20:13:27.600929
21	consumable	1	73	1	2026-07-29 20:13:27.600934	2026-07-29 20:13:27.60094
21	consumable	2	76	1	2026-07-29 20:13:27.600945	2026-07-29 20:13:27.60095
21	consumable	3	86	1	2026-07-29 20:13:27.600956	2026-07-29 20:13:27.600961
21	hold	1	134	2000	2026-07-29 20:13:27.600967	2026-07-29 20:13:27.600972
21	hold	2	105	500	2026-07-29 20:13:27.600978	2026-07-29 20:13:27.600983
21	hold	3	127	800	2026-07-29 20:13:27.600989	2026-07-29 20:13:27.600994
22	lantern	1	48	\N	2026-07-29 20:16:46.10524	2026-07-29 20:16:46.105245
22	upgrade	1	37	\N	2026-07-29 20:16:46.105251	2026-07-29 20:16:46.105257
22	upgrade	2	22	\N	2026-07-29 20:16:46.105262	2026-07-29 20:16:46.105267
22	upgrade	3	20	\N	2026-07-29 20:16:46.105273	2026-07-29 20:16:46.105278
22	upgrade	4	11	\N	2026-07-29 20:16:46.105284	2026-07-29 20:16:46.105289
22	upgrade	5	36	\N	2026-07-29 20:16:46.105295	2026-07-29 20:16:46.105301
22	upgrade	6	40	\N	2026-07-29 20:16:46.105306	2026-07-29 20:16:46.105312
22	weapon_port	1	161	20	2026-07-29 20:16:46.105317	2026-07-29 20:16:46.105323
22	weapon_starboard	1	161	20	2026-07-29 20:16:46.105328	2026-07-29 20:16:46.105333
22	special_crew	1	216	1	2026-07-29 20:16:46.105339	2026-07-29 20:16:46.105344
22	special_crew	2	219	1	2026-07-29 20:16:46.10535	2026-07-29 20:16:46.105355
22	special_crew	3	222	1	2026-07-29 20:16:46.105361	2026-07-29 20:16:46.105366
22	special_crew	4	192	1	2026-07-29 20:16:46.105371	2026-07-29 20:16:46.105376
22	ammunition	1	229	2000	2026-07-29 20:16:46.105382	2026-07-29 20:16:46.105387
22	consumable	1	68	1	2026-07-29 20:16:46.105393	2026-07-29 20:16:46.105399
22	consumable	2	77	1	2026-07-29 20:16:46.105404	2026-07-29 20:16:46.10541
22	consumable	3	86	1	2026-07-29 20:16:46.105415	2026-07-29 20:16:46.10542
22	hold	1	134	2000	2026-07-29 20:16:46.105426	2026-07-29 20:16:46.105431
22	hold	2	105	500	2026-07-29 20:16:46.105437	2026-07-29 20:16:46.105442
22	hold	3	127	800	2026-07-29 20:16:46.105448	2026-07-29 20:16:46.105453
23	sail	1	3	\N	2026-07-29 20:30:05.586455	2026-07-29 20:30:05.586477
23	lantern	1	48	\N	2026-07-29 20:30:05.586483	2026-07-29 20:30:05.586489
23	upgrade	1	37	\N	2026-07-29 20:30:05.586495	2026-07-29 20:30:05.5865
23	upgrade	2	27	\N	2026-07-29 20:30:05.586505	2026-07-29 20:30:05.58651
23	upgrade	3	39	\N	2026-07-29 20:30:05.586516	2026-07-29 20:30:05.586521
23	upgrade	4	34	\N	2026-07-29 20:30:05.586526	2026-07-29 20:30:05.586531
23	upgrade	5	38	\N	2026-07-29 20:30:05.586537	2026-07-29 20:30:05.586542
23	upgrade	6	36	\N	2026-07-29 20:30:05.586547	2026-07-29 20:30:05.586552
23	weapon_port	1	161	8	2026-07-29 20:30:05.586558	2026-07-29 20:30:05.586563
23	weapon_starboard	1	161	8	2026-07-29 20:30:05.586568	2026-07-29 20:30:05.586573
23	weapon_mortar	1	158	2	2026-07-29 20:30:05.586579	2026-07-29 20:30:05.586584
23	special_crew	1	179	1	2026-07-29 20:30:05.586589	2026-07-29 20:30:05.586594
23	special_crew	2	220	1	2026-07-29 20:30:05.5866	2026-07-29 20:30:05.586605
23	special_crew	3	216	1	2026-07-29 20:30:05.58661	2026-07-29 20:30:05.586615
23	special_crew	4	222	1	2026-07-29 20:30:05.586621	2026-07-29 20:30:05.586626
23	ammunition	1	229	2000	2026-07-29 20:30:05.586632	2026-07-29 20:30:05.586637
23	ammunition	2	64	100	2026-07-29 20:30:05.586643	2026-07-29 20:30:05.586649
23	consumable	1	87	1	2026-07-29 20:30:05.586655	2026-07-29 20:30:05.58666
23	consumable	2	68	1	2026-07-29 20:30:05.586665	2026-07-29 20:30:05.586671
23	consumable	3	86	1	2026-07-29 20:30:05.586676	2026-07-29 20:30:05.586681
23	hold	1	134	1000	2026-07-29 20:30:05.586686	2026-07-29 20:30:05.586691
23	hold	2	105	200	2026-07-29 20:30:05.586697	2026-07-29 20:30:05.586702
23	hold	3	127	400	2026-07-29 20:30:05.586707	2026-07-29 20:30:05.586713
24	sail	1	3	\N	2026-07-29 20:35:07.326922	2026-07-29 20:35:07.326945
24	lantern	1	48	\N	2026-07-29 20:35:07.326952	2026-07-29 20:35:07.326958
24	upgrade	1	37	\N	2026-07-29 20:35:07.326964	2026-07-29 20:35:07.32697
24	upgrade	2	25	\N	2026-07-29 20:35:07.326975	2026-07-29 20:35:07.326981
24	upgrade	3	27	\N	2026-07-29 20:35:07.326986	2026-07-29 20:35:07.326991
24	upgrade	4	38	\N	2026-07-29 20:35:07.326997	2026-07-29 20:35:07.327002
24	upgrade	5	36	\N	2026-07-29 20:35:07.327007	2026-07-29 20:35:07.327013
24	upgrade	6	34	\N	2026-07-29 20:35:07.327018	2026-07-29 20:35:07.327023
24	weapon_port	1	161	8	2026-07-29 20:35:07.327029	2026-07-29 20:35:07.327034
24	weapon_starboard	1	161	8	2026-07-29 20:35:07.327039	2026-07-29 20:35:07.327044
24	weapon_mortar	1	164	2	2026-07-29 20:35:07.32705	2026-07-29 20:35:07.327055
24	special_crew	1	179	1	2026-07-29 20:35:07.32706	2026-07-29 20:35:07.327065
24	special_crew	2	220	1	2026-07-29 20:35:07.327071	2026-07-29 20:35:07.327076
24	special_crew	3	222	1	2026-07-29 20:35:07.327082	2026-07-29 20:35:07.327087
24	special_crew	4	216	1	2026-07-29 20:35:07.327093	2026-07-29 20:35:07.327098
24	ammunition	1	229	1000	2026-07-29 20:35:07.327103	2026-07-29 20:35:07.327108
24	ammunition	2	61	100	2026-07-29 20:35:07.327114	2026-07-29 20:35:07.327119
24	consumable	1	87	1	2026-07-29 20:35:07.327124	2026-07-29 20:35:07.327129
24	consumable	2	68	1	2026-07-29 20:35:07.327135	2026-07-29 20:35:07.32714
24	consumable	3	86	1	2026-07-29 20:35:07.327145	2026-07-29 20:35:07.327151
24	hold	1	134	1000	2026-07-29 20:35:07.327156	2026-07-29 20:35:07.327161
24	hold	2	105	300	2026-07-29 20:35:07.327167	2026-07-29 20:35:07.327172
24	hold	3	127	600	2026-07-29 20:35:07.327178	2026-07-29 20:35:07.327183
25	sail	1	3	\N	2026-07-29 21:00:33.928642	2026-07-29 21:00:33.928671
25	lantern	1	48	\N	2026-07-29 21:00:33.928682	2026-07-29 21:00:33.928691
25	upgrade	1	37	\N	2026-07-29 21:00:33.928701	2026-07-29 21:00:33.928709
25	upgrade	2	15	\N	2026-07-29 21:00:33.928765	2026-07-29 21:00:33.928777
25	upgrade	3	23	\N	2026-07-29 21:00:33.928787	2026-07-29 21:00:33.928796
25	upgrade	4	38	\N	2026-07-29 21:00:33.928805	2026-07-29 21:00:33.928813
25	upgrade	5	36	\N	2026-07-29 21:00:33.928822	2026-07-29 21:00:33.92883
25	upgrade	6	40	\N	2026-07-29 21:00:33.928839	2026-07-29 21:00:33.928848
25	weapon_port	1	152	1	2026-07-29 21:00:33.928857	2026-07-29 21:00:33.928865
25	weapon_port	2	149	1	2026-07-29 21:00:33.928874	2026-07-29 21:00:33.928883
25	weapon_starboard	1	152	1	2026-07-29 21:00:33.928892	2026-07-29 21:00:33.9289
25	weapon_starboard	2	149	1	2026-07-29 21:00:33.928909	2026-07-29 21:00:33.928918
25	special_crew	1	222	1	2026-07-29 21:00:33.928927	2026-07-29 21:00:33.928935
25	special_crew	2	219	1	2026-07-29 21:00:33.928945	2026-07-29 21:00:33.928953
25	special_crew	3	216	1	2026-07-29 21:00:33.928962	2026-07-29 21:00:33.928971
25	special_crew	4	225	1	2026-07-29 21:00:33.92898	2026-07-29 21:00:33.928988
25	ammunition	1	229	1000	2026-07-29 21:00:33.928997	2026-07-29 21:00:33.929006
25	consumable	1	73	1	2026-07-29 21:00:33.929015	2026-07-29 21:00:33.929024
25	consumable	2	86	1	2026-07-29 21:00:33.929032	2026-07-29 21:00:33.929041
25	consumable	3	84	1	2026-07-29 21:00:33.92905	2026-07-29 21:00:33.929058
25	hold	1	134	1000	2026-07-29 21:00:33.929067	2026-07-29 21:00:33.929075
25	hold	2	105	200	2026-07-29 21:00:33.929084	2026-07-29 21:00:33.929093
25	hold	3	127	400	2026-07-29 21:00:33.929101	2026-07-29 21:00:33.92911
26	sail	1	3	\N	2026-07-29 21:03:48.753648	2026-07-29 21:03:48.753671
26	lantern	1	48	\N	2026-07-29 21:03:48.753678	2026-07-29 21:03:48.753684
26	upgrade	1	37	\N	2026-07-29 21:03:48.75369	2026-07-29 21:03:48.753696
26	upgrade	2	22	\N	2026-07-29 21:03:48.753701	2026-07-29 21:03:48.753707
26	upgrade	3	20	\N	2026-07-29 21:03:48.753713	2026-07-29 21:03:48.753718
26	upgrade	4	11	\N	2026-07-29 21:03:48.753724	2026-07-29 21:03:48.75373
26	upgrade	5	36	\N	2026-07-29 21:03:48.753735	2026-07-29 21:03:48.753741
26	upgrade	6	40	\N	2026-07-29 21:03:48.753747	2026-07-29 21:03:48.753753
26	weapon_port	1	152	1	2026-07-29 21:03:48.753758	2026-07-29 21:03:48.753763
26	weapon_port	2	149	1	2026-07-29 21:03:48.753769	2026-07-29 21:03:48.753774
26	weapon_starboard	1	152	1	2026-07-29 21:03:48.753779	2026-07-29 21:03:48.753784
26	weapon_starboard	2	149	1	2026-07-29 21:03:48.75379	2026-07-29 21:03:48.753795
26	special_crew	1	222	1	2026-07-29 21:03:48.753801	2026-07-29 21:03:48.753806
26	special_crew	2	219	1	2026-07-29 21:03:48.753811	2026-07-29 21:03:48.753816
26	special_crew	3	216	1	2026-07-29 21:03:48.753821	2026-07-29 21:03:48.753826
26	special_crew	4	192	1	2026-07-29 21:03:48.753832	2026-07-29 21:03:48.753837
26	ammunition	1	229	1000	2026-07-29 21:03:48.753842	2026-07-29 21:03:48.753847
26	consumable	1	73	1	2026-07-29 21:03:48.753853	2026-07-29 21:03:48.753858
26	consumable	2	77	1	2026-07-29 21:03:48.753863	2026-07-29 21:03:48.753868
26	consumable	3	86	1	2026-07-29 21:03:48.753874	2026-07-29 21:03:48.753879
26	hold	1	134	1000	2026-07-29 21:03:48.753884	2026-07-29 21:03:48.753889
26	hold	2	105	300	2026-07-29 21:03:48.753895	2026-07-29 21:03:48.7539
26	hold	3	127	500	2026-07-29 21:03:48.753905	2026-07-29 21:03:48.75391
27	sail	1	3	\N	2026-07-29 21:08:11.586277	2026-07-29 21:08:11.586299
27	lantern	1	48	\N	2026-07-29 21:08:11.586307	2026-07-29 21:08:11.586312
27	upgrade	1	37	\N	2026-07-29 21:08:11.586318	2026-07-29 21:08:11.586323
27	upgrade	2	27	\N	2026-07-29 21:08:11.586329	2026-07-29 21:08:11.586334
27	upgrade	3	39	\N	2026-07-29 21:08:11.586339	2026-07-29 21:08:11.586344
27	upgrade	4	34	\N	2026-07-29 21:08:11.58635	2026-07-29 21:08:11.586356
27	upgrade	5	36	\N	2026-07-29 21:08:11.586362	2026-07-29 21:08:11.586367
27	upgrade	6	38	\N	2026-07-29 21:08:11.586372	2026-07-29 21:08:11.586377
27	weapon_port	1	161	7	2026-07-29 21:08:11.586383	2026-07-29 21:08:11.586388
27	weapon_starboard	1	161	7	2026-07-29 21:08:11.586394	2026-07-29 21:08:11.586399
27	weapon_mortar	1	155	1	2026-07-29 21:08:11.586404	2026-07-29 21:08:11.586409
27	special_crew	1	179	1	2026-07-29 21:08:11.586415	2026-07-29 21:08:11.58642
27	special_crew	2	220	1	2026-07-29 21:08:11.586425	2026-07-29 21:08:11.58643
27	special_crew	3	216	1	2026-07-29 21:08:11.586436	2026-07-29 21:08:11.586441
27	special_crew	4	222	1	2026-07-29 21:08:11.586446	2026-07-29 21:08:11.586451
27	ammunition	1	229	700	2026-07-29 21:08:11.586457	2026-07-29 21:08:11.586462
27	ammunition	2	64	60	2026-07-29 21:08:11.586467	2026-07-29 21:08:11.586472
27	consumable	1	87	1	2026-07-29 21:08:11.586477	2026-07-29 21:08:11.586482
27	consumable	2	73	1	2026-07-29 21:08:11.586488	2026-07-29 21:08:11.586493
27	consumable	3	86	1	2026-07-29 21:08:11.586498	2026-07-29 21:08:11.586503
27	hold	1	134	1000	2026-07-29 21:08:11.586508	2026-07-29 21:08:11.586513
27	hold	2	105	300	2026-07-29 21:08:11.586519	2026-07-29 21:08:11.586524
27	hold	3	127	500	2026-07-29 21:08:11.586529	2026-07-29 21:08:11.586534
28	sail	1	3	\N	2026-07-29 21:10:43.739773	2026-07-29 21:10:43.739796
28	lantern	1	48	\N	2026-07-29 21:10:43.739803	2026-07-29 21:10:43.739808
28	upgrade	1	37	\N	2026-07-29 21:10:43.739814	2026-07-29 21:10:43.73982
28	upgrade	2	25	\N	2026-07-29 21:10:43.739826	2026-07-29 21:10:43.739831
28	upgrade	3	27	\N	2026-07-29 21:10:43.739836	2026-07-29 21:10:43.739842
28	upgrade	4	38	\N	2026-07-29 21:10:43.739848	2026-07-29 21:10:43.739854
28	upgrade	5	34	\N	2026-07-29 21:10:43.739859	2026-07-29 21:10:43.739865
28	upgrade	6	36	\N	2026-07-29 21:10:43.739871	2026-07-29 21:10:43.739877
28	weapon_port	1	161	7	2026-07-29 21:10:43.739882	2026-07-29 21:10:43.739888
28	weapon_starboard	1	161	7	2026-07-29 21:10:43.739894	2026-07-29 21:10:43.739899
28	weapon_mortar	1	164	1	2026-07-29 21:10:43.739905	2026-07-29 21:10:43.73991
28	special_crew	1	179	1	2026-07-29 21:10:43.739916	2026-07-29 21:10:43.739921
28	special_crew	2	220	1	2026-07-29 21:10:43.739927	2026-07-29 21:10:43.739932
28	special_crew	3	216	1	2026-07-29 21:10:43.739938	2026-07-29 21:10:43.739943
28	special_crew	4	222	1	2026-07-29 21:10:43.739948	2026-07-29 21:10:43.739954
28	ammunition	1	229	700	2026-07-29 21:10:43.739959	2026-07-29 21:10:43.739964
28	ammunition	2	61	50	2026-07-29 21:10:43.73997	2026-07-29 21:10:43.739975
28	consumable	1	87	1	2026-07-29 21:10:43.739981	2026-07-29 21:10:43.739986
28	consumable	2	73	1	2026-07-29 21:10:43.739992	2026-07-29 21:10:43.739997
28	consumable	3	86	1	2026-07-29 21:10:43.740003	2026-07-29 21:10:43.740008
28	hold	1	134	1000	2026-07-29 21:10:43.740013	2026-07-29 21:10:43.740018
28	hold	2	105	300	2026-07-29 21:10:43.740024	2026-07-29 21:10:43.740029
28	hold	3	127	500	2026-07-29 21:10:43.740035	2026-07-29 21:10:43.74004
29	sail	1	3	\N	2026-07-29 21:35:54.755466	2026-07-29 21:35:54.755489
29	lantern	1	44	\N	2026-07-29 21:35:54.755496	2026-07-29 21:35:54.755501
29	upgrade	1	37	\N	2026-07-29 21:35:54.755507	2026-07-29 21:35:54.755513
29	upgrade	2	33	\N	2026-07-29 21:35:54.755518	2026-07-29 21:35:54.755523
29	upgrade	3	14	\N	2026-07-29 21:35:54.755529	2026-07-29 21:35:54.755535
29	upgrade	4	26	\N	2026-07-29 21:35:54.755541	2026-07-29 21:35:54.755546
29	upgrade	5	20	\N	2026-07-29 21:35:54.755553	2026-07-29 21:35:54.755558
29	upgrade	6	22	\N	2026-07-29 21:35:54.755564	2026-07-29 21:35:54.755569
29	upgrade	7	31	\N	2026-07-29 21:35:54.755574	2026-07-29 21:35:54.755579
29	weapon_front	1	173	4	2026-07-29 21:35:54.755585	2026-07-29 21:35:54.75559
29	weapon_port	1	149	1	2026-07-29 21:35:54.755595	2026-07-29 21:35:54.7556
29	weapon_port	2	152	1	2026-07-29 21:35:54.755606	2026-07-29 21:35:54.755611
29	weapon_starboard	1	149	1	2026-07-29 21:35:54.755616	2026-07-29 21:35:54.755621
29	weapon_starboard	2	152	1	2026-07-29 21:35:54.755627	2026-07-29 21:35:54.755632
29	special_crew	1	189	1	2026-07-29 21:35:54.755638	2026-07-29 21:35:54.755643
29	special_crew	2	207	1	2026-07-29 21:35:54.755648	2026-07-29 21:35:54.755653
29	special_crew	3	216	1	2026-07-29 21:35:54.755658	2026-07-29 21:35:54.755663
29	special_crew	4	183	1	2026-07-29 21:35:54.755669	2026-07-29 21:35:54.755674
29	ammunition	1	229	2000	2026-07-29 21:35:54.755679	2026-07-29 21:35:54.755684
29	ammunition	2	230	2000	2026-07-29 21:35:54.755689	2026-07-29 21:35:54.755694
29	ammunition	3	51	1000	2026-07-29 21:35:54.7557	2026-07-29 21:35:54.755705
29	consumable	1	86	1	2026-07-29 21:35:54.75571	2026-07-29 21:35:54.755715
29	consumable	2	75	1	2026-07-29 21:35:54.755721	2026-07-29 21:35:54.755726
29	consumable	3	69	1	2026-07-29 21:35:54.755731	2026-07-29 21:35:54.755736
29	hold	1	134	1000	2026-07-29 21:35:54.755741	2026-07-29 21:35:54.755746
29	hold	2	105	300	2026-07-29 21:35:54.755752	2026-07-29 21:35:54.755756
29	hold	3	127	400	2026-07-29 21:35:54.755762	2026-07-29 21:35:54.755767
\.

CREATE TEMP TABLE _rbf_build_classification_stage (
    old_build_id integer NOT NULL,
    tag varchar(40) NOT NULL,
    PRIMARY KEY (old_build_id, tag)
) ON COMMIT DROP;

COPY _rbf_build_classification_stage (old_build_id, tag) FROM stdin;
2	pvp_group
2	pvp_solo
4	fast
4	pve_group
4	pve_solo
4	transport
5	pve_solo
5	pve_group
5	combat
5	pve_instanced
5	pvp_solo
5	pvp_group
6	port_battle
6	imperial
7	port_battle
7	heavy
8	port_battle
8	siege
9	port_battle
9	combat
10	port_battle
10	heavy
11	port_battle
11	heavy
12	port_battle
12	siege
13	port_battle
13	siege
14	port_battle
14	imperial
15	port_battle
15	heavy
16	port_battle
16	siege
17	port_battle
17	heavy
18	port_battle
18	heavy
19	port_battle
19	siege
20	port_battle
20	siege
21	port_battle
21	heavy
22	port_battle
22	heavy
23	port_battle
23	siege
24	port_battle
24	siege
25	port_battle
25	combat
26	port_battle
26	combat
27	port_battle
27	siege
28	port_battle
28	siege
29	pvp_solo
29	pvp_group
29	pvp_instanced
29	fast
\.

-- -------------------------------------------------------------------------
-- 1. Target schema contract
-- -------------------------------------------------------------------------
DO $$
DECLARE
    missing text;
BEGIN
    WITH required(table_name, column_name) AS (
        VALUES
          ('builds','id'), ('builds','build_name'), ('builds','build_type'),
          ('builds','ship_id'), ('builds','owner_id'),
          ('builds','is_official_template'), ('builds','sailors'),
          ('builds','soldiers'), ('builds','musketeers'),
          ('builds','mercenaries'), ('builds','details'),
          ('builds','created_at'), ('builds','updated_at'),
          ('builds','mortar_modification_installed'),
          ('builds','research_upgrade_feature_id'),
          ('build_slots','id'), ('build_slots','build_id'),
          ('build_slots','slot_type'), ('build_slots','slot_index'),
          ('build_slots','option_id'), ('build_slots','quantity'),
          ('build_slots','created_at'), ('build_slots','updated_at'),
          ('build_classifications','build_id'), ('build_classifications','tag'),
          ('users','id'), ('users','username'),
          ('ships','id'), ('ships','name'), ('ships','seed_key'),
          ('ships','has_lantern'), ('ships','upgrade_slots'),
          ('build_item_categories','id'), ('build_item_categories','key'),
          ('build_item_options','id'), ('build_item_options','category_id'),
          ('build_item_options','name'), ('build_item_options','seed_key'),
          ('build_item_options','option_kind'),
          ('build_item_options','weapon_class_id'),
          ('build_item_options','weapon_caliber_inches'),
          ('build_item_option_slot_types','option_id'),
          ('build_item_option_slot_types','slot_type_id'),
          ('build_item_effects','option_id'),
          ('build_item_effects','effect_key'),
          ('build_item_effects','effect_value'),
          ('build_roles','slug'),
          ('build_features','id'), ('build_features','code'),
          ('build_features','upgrade_slots_granted'),
          ('weapon_slot_types','id'), ('weapon_slot_types','code'),
          ('weapon_classes','id'), ('weapon_classes','rank'),
          ('ship_weapon_mounts','ship_id'),
          ('ship_weapon_mounts','slot_type_id'),
          ('ship_weapon_mounts','capacity'),
          ('ship_weapon_mounts','special_weapon_capacity'),
          ('ship_weapon_mounts','max_weapon_class_id'),
          ('ship_weapon_mounts','max_caliber_inches'),
          ('ship_mortar_modifications','ship_id'),
          ('ship_mortar_modifications','mortar_capacity'),
          ('ship_mortar_modifications','max_caliber_inches'),
          ('ship_mortar_modifications','broadside_capacity_delta'),
          ('ship_upgrade_effect_overrides','ship_id'),
          ('ship_upgrade_effect_overrides','option_id'),
          ('ship_upgrade_effect_overrides','effect_key'),
          ('ship_upgrade_effect_overrides','effect_value')
    )
    SELECT string_agg(
               r.table_name || '.' || r.column_name,
               ', ' ORDER BY r.table_name, r.column_name
           )
      INTO missing
      FROM required r
      LEFT JOIN information_schema.columns c
        ON c.table_schema='public'
       AND c.table_name=r.table_name
       AND c.column_name=r.column_name
     WHERE c.column_name IS NULL;

    IF missing IS NOT NULL THEN
        RAISE EXCEPTION
          'Target schema is incompatible; missing columns: %', missing;
    END IF;
END $$;

-- -------------------------------------------------------------------------
-- 2. Source-stage consistency
-- -------------------------------------------------------------------------
DO $$
DECLARE
    problem text;
BEGIN
    IF (SELECT count(*) FROM _rbf_build_stage) <> 27
       OR (SELECT count(*) FROM _rbf_build_slot_stage) <> 625
       OR (SELECT count(*) FROM _rbf_build_classification_stage) <> 62 THEN
        RAISE EXCEPTION 'Unexpected logical backup row counts.';
    END IF;

    SELECT string_agg(DISTINCT b.old_build_id::text, ', ' ORDER BY b.old_build_id::text)
      INTO problem
      FROM _rbf_build_stage b
      LEFT JOIN _rbf_ship_stage s ON s.source_ship_id=b.source_ship_id
     WHERE s.source_ship_id IS NULL;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Builds reference missing staged ships: %', problem;
    END IF;

    SELECT string_agg(DISTINCT st.source_option_id::text, ', ' ORDER BY st.source_option_id::text)
      INTO problem
      FROM _rbf_build_slot_stage st
      LEFT JOIN _rbf_option_stage o ON o.source_option_id=st.source_option_id
     WHERE o.source_option_id IS NULL;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Slots reference missing staged options: %', problem;
    END IF;

    SELECT string_agg(
               DISTINCT st.old_build_id || ':' || st.slot_type || ':' || st.slot_index,
               ', '
           )
      INTO problem
      FROM _rbf_build_slot_stage st
      JOIN _rbf_option_stage o ON o.source_option_id=st.source_option_id
     WHERE o.category_key <> CASE
             WHEN left(st.slot_type,7)='weapon_' THEN 'weapon'
             ELSE st.slot_type
         END;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Source slot/category mismatch: %', problem;
    END IF;

    SELECT string_agg(old_build_id::text, ', ' ORDER BY old_build_id::text)
      INTO problem
      FROM (
          SELECT old_build_id
            FROM _rbf_build_classification_stage
           GROUP BY old_build_id
          HAVING count(*) > 6
      ) x;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Builds exceed the six-classification limit: %', problem;
    END IF;

    SELECT string_agg(DISTINCT tag, ', ' ORDER BY tag)
      INTO problem
      FROM _rbf_build_classification_stage
     WHERE tag NOT IN (
         'port_battle','pve_solo','pve_group','pve_instanced',
         'pvp_solo','pvp_group','pvp_instanced','trading',
         'fast','combat','heavy','transport','siege','imperial'
     );
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Unsupported build classifications: %', problem;
    END IF;

    SELECT string_agg(DISTINCT slot_type, ', ' ORDER BY slot_type)
      INTO problem
      FROM _rbf_build_slot_stage
     WHERE slot_type NOT IN (
         'sail','upgrade','lantern','special_crew','ammunition',
         'consumable','hold','weapon_front','weapon_rear','weapon_port',
         'weapon_starboard','weapon_mortar','weapon_special'
     );
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Unsupported slot types: %', problem;
    END IF;

    SELECT string_agg(old_build_id::text, ', ' ORDER BY old_build_id::text)
      INTO problem
      FROM (
          SELECT old_build_id
            FROM _rbf_build_slot_stage
           WHERE slot_type='sail'
           GROUP BY old_build_id
          HAVING count(*) > 1
      ) x;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Builds contain multiple sail rows: %', problem;
    END IF;

    SELECT string_agg(old_build_id::text, ', ' ORDER BY old_build_id::text)
      INTO problem
      FROM (
          SELECT old_build_id
            FROM _rbf_build_slot_stage
           WHERE slot_type='lantern'
           GROUP BY old_build_id
          HAVING count(*) > 1
      ) x;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Builds contain multiple lantern rows: %', problem;
    END IF;

    SELECT string_agg(old_build_id::text, ', ' ORDER BY old_build_id::text)
      INTO problem
      FROM (
          SELECT old_build_id
            FROM _rbf_build_slot_stage
           WHERE slot_type='special_crew'
           GROUP BY old_build_id
          HAVING count(*) > 5
      ) x;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Builds exceed five specialist rows: %', problem;
    END IF;

    SELECT string_agg(old_build_id::text, ', ' ORDER BY old_build_id::text)
      INTO problem
      FROM (
          SELECT old_build_id
            FROM _rbf_build_slot_stage
           WHERE slot_type='consumable'
           GROUP BY old_build_id
          HAVING count(*) > 3
      ) x;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Builds exceed three consumable rows: %', problem;
    END IF;
END $$;

-- -------------------------------------------------------------------------
-- 3. Resolve users, ships and options without carrying numeric IDs
-- -------------------------------------------------------------------------
CREATE TEMP TABLE _rbf_owner_resolution (
    source_username text PRIMARY KEY,
    target_username text NOT NULL,
    target_user_id integer NOT NULL
) ON COMMIT DROP;

DO $$
DECLARE
    r record;
    match_count integer;
    target_id integer;
BEGIN
    FOR r IN SELECT * FROM _rbf_owner_map ORDER BY source_username LOOP
        SELECT count(*), min(id)
          INTO match_count, target_id
          FROM public.users
         WHERE username=r.target_username;

        IF match_count <> 1 THEN
            RAISE EXCEPTION
              'Owner mapping % -> % resolved to % users. '
              'Provide -v owner_%=<existing-user>.',
              r.source_username, r.target_username, match_count,
              replace(r.source_username, '-', '_');
        END IF;

        INSERT INTO _rbf_owner_resolution
        VALUES (r.source_username, r.target_username, target_id);
    END LOOP;
END $$;

CREATE TEMP TABLE _rbf_ship_resolution (
    source_ship_id integer PRIMARY KEY,
    target_ship_id integer NOT NULL
) ON COMMIT DROP;

DO $$
DECLARE
    r record;
    match_count integer;
    target_id integer;
BEGIN
    FOR r IN SELECT * FROM _rbf_ship_stage ORDER BY source_ship_id LOOP
        SELECT count(DISTINCT s.id), min(s.id)
          INTO match_count, target_id
          FROM public.ships s
         WHERE (r.legacy_seed_key IS NOT NULL
                AND lower(s.seed_key)=lower(r.legacy_seed_key))
            OR lower(s.seed_key)=lower(r.current_seed_key)
            OR lower(s.name)=lower(r.ship_name);

        IF match_count <> 1 THEN
            RAISE EXCEPTION
              'Ship "%" (legacy %, current %) resolved to % target rows.',
              r.ship_name, r.legacy_seed_key, r.current_seed_key, match_count;
        END IF;

        INSERT INTO _rbf_ship_resolution VALUES (r.source_ship_id, target_id);
    END LOOP;
END $$;

CREATE TEMP TABLE _rbf_option_resolution (
    source_option_id integer PRIMARY KEY,
    target_option_id integer NOT NULL
) ON COMMIT DROP;

DO $$
DECLARE
    r record;
    match_count integer;
    target_id integer;
BEGIN
    FOR r IN SELECT * FROM _rbf_option_stage ORDER BY source_option_id LOOP
        SELECT count(DISTINCT o.id), min(o.id)
          INTO match_count, target_id
          FROM public.build_item_options o
          JOIN public.build_item_categories c ON c.id=o.category_id
         WHERE (r.legacy_seed_key IS NOT NULL
                AND lower(o.seed_key)=lower(r.legacy_seed_key))
            OR lower(o.seed_key)=lower(r.current_seed_key)
            OR (
                c.key=r.category_key
                AND lower(o.name)=lower(r.option_name)
            );

        IF match_count <> 1 THEN
            RAISE EXCEPTION
              'Build option "%/%" (legacy %, current %) resolved to % target rows.',
              r.category_key, r.option_name,
              r.legacy_seed_key, r.current_seed_key, match_count;
        END IF;

        INSERT INTO _rbf_option_resolution VALUES (r.source_option_id, target_id);
    END LOOP;
END $$;

\echo 'Reference resolution summary:'
SELECT
    (SELECT count(*) FROM _rbf_ship_resolution) AS ships_resolved,
    (SELECT count(*) FROM _rbf_option_resolution) AS options_resolved,
    (SELECT count(*) FROM _rbf_owner_resolution) AS owners_resolved;

\echo 'Owner mapping:'
SELECT source_username AS source_owner,
       target_username AS target_owner,
       target_user_id
  FROM _rbf_owner_resolution
 ORDER BY source_username;

-- -------------------------------------------------------------------------
-- 4. Remaining logical/FK contract checks
-- -------------------------------------------------------------------------
DO $$
DECLARE
    problem text;
BEGIN
    SELECT string_agg(DISTINCT b.build_type, ', ' ORDER BY b.build_type)
      INTO problem
      FROM _rbf_build_stage b
      LEFT JOIN public.build_roles r ON r.slug=b.build_type
     WHERE r.slug IS NULL;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Missing target build roles: %', problem;
    END IF;

    SELECT string_agg(
               DISTINCT b.research_feature_code,
               ', ' ORDER BY b.research_feature_code
           )
      INTO problem
      FROM _rbf_build_stage b
      LEFT JOIN public.build_features f ON f.code=b.research_feature_code
     WHERE b.research_feature_code IS NOT NULL
       AND f.id IS NULL;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Missing target build features: %', problem;
    END IF;

    -- Technical seed identity and semantic identity may differ because of a
    -- legitimate seed override, but all available identities must have
    -- resolved to the SAME target row (enforced by the resolution count).
    -- Here we additionally verify that every mapped option's target category
    -- still matches the persisted slot semantics.
    SELECT string_agg(
               DISTINCT st.old_build_id || ':' || st.slot_type || ':' || st.slot_index,
               ', '
           )
      INTO problem
      FROM _rbf_build_slot_stage st
      JOIN _rbf_option_resolution om
        ON om.source_option_id=st.source_option_id
      JOIN public.build_item_options o ON o.id=om.target_option_id
      JOIN public.build_item_categories c ON c.id=o.category_id
     WHERE c.key <> CASE
             WHEN left(st.slot_type,7)='weapon_' THEN 'weapon'
             ELSE st.slot_type
         END;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Target option category conflicts with slot semantics: %',
            problem;
    END IF;

    -- Current Java requires unique item names within each inventory/mount list.
    SELECT string_agg(old_build_id || ':' || slot_type, ', ' ORDER BY old_build_id || ':' || slot_type)
      INTO problem
      FROM (
          SELECT st.old_build_id, st.slot_type
            FROM _rbf_build_slot_stage st
            JOIN _rbf_option_resolution om
              ON om.source_option_id=st.source_option_id
           GROUP BY st.old_build_id, st.slot_type, om.target_option_id
          HAVING count(*) > 1
      ) x;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Duplicate target items inside a build slot list: %', problem;
    END IF;

    -- Lantern builds must still point at a ship with a lantern.
    SELECT string_agg(DISTINCT b.old_build_id::text, ', ' ORDER BY b.old_build_id::text)
      INTO problem
      FROM _rbf_build_stage b
      JOIN _rbf_ship_resolution sm ON sm.source_ship_id=b.source_ship_id
      JOIN public.ships s ON s.id=sm.target_ship_id
     WHERE s.has_lantern=false
       AND EXISTS (
           SELECT 1 FROM _rbf_build_slot_stage st
            WHERE st.old_build_id=b.old_build_id
              AND st.slot_type='lantern'
       );
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Target ships no longer support required lantern slots for builds: %',
            problem;
    END IF;
END $$;

-- -------------------------------------------------------------------------
-- 5. Target weapon compatibility/capacity
-- -------------------------------------------------------------------------
DO $$
DECLARE
    problem text;
BEGIN
    -- Every weapon row must retain the target option->slot compatibility link.
    SELECT string_agg(
               DISTINCT st.old_build_id || ':' || st.slot_type || ':' || st.slot_index,
               ', '
           )
      INTO problem
      FROM _rbf_build_slot_stage st
      JOIN _rbf_option_resolution om ON om.source_option_id=st.source_option_id
      JOIN public.weapon_slot_types wt ON wt.code=st.slot_type
      LEFT JOIN public.build_item_option_slot_types link
        ON link.option_id=om.target_option_id
       AND link.slot_type_id=wt.id
     WHERE left(st.slot_type,7)='weapon_'
       AND link.option_id IS NULL;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Target weapon option is no longer allowed in its stored slot: %',
            problem;
    END IF;

    -- Reproduce the current Java compatibility rules against target master data.
    WITH weapon_rows AS (
        SELECT st.old_build_id, st.slot_type, st.slot_index,
               coalesce(st.quantity,1) AS quantity,
               o.name AS option_name, o.option_kind,
               o.weapon_caliber_inches,
               owc.rank AS option_class_rank,
               m.capacity AS mount_capacity,
               m.special_weapon_capacity,
               mwc.rank AS mount_class_rank,
               m.max_caliber_inches AS mount_max_caliber,
               mm.mortar_capacity,
               mm.max_caliber_inches AS mod_max_caliber,
               mm.broadside_capacity_delta,
               b.mortar_modification_installed
          FROM _rbf_build_slot_stage st
          JOIN _rbf_build_stage b ON b.old_build_id=st.old_build_id
          JOIN _rbf_ship_resolution sm ON sm.source_ship_id=b.source_ship_id
          JOIN _rbf_option_resolution om ON om.source_option_id=st.source_option_id
          JOIN public.build_item_options o ON o.id=om.target_option_id
          LEFT JOIN public.weapon_classes owc ON owc.id=o.weapon_class_id
          LEFT JOIN public.weapon_slot_types wt ON wt.code=st.slot_type
          LEFT JOIN public.ship_weapon_mounts m
            ON m.ship_id=sm.target_ship_id
           AND m.slot_type_id=wt.id
          LEFT JOIN public.weapon_classes mwc ON mwc.id=m.max_weapon_class_id
          LEFT JOIN public.ship_mortar_modifications mm
            ON mm.ship_id=sm.target_ship_id
         WHERE left(st.slot_type,7)='weapon_'
    ), checked AS (
        SELECT *,
               CASE
                   WHEN mount_capacity IS NULL THEN 0
                   WHEN mortar_modification_installed
                        AND slot_type='weapon_mortar'
                       THEN mount_capacity + coalesce(mortar_capacity,0)
                   WHEN mortar_modification_installed
                        AND slot_type IN ('weapon_port','weapon_starboard')
                       THEN greatest(0, mount_capacity + coalesce(broadside_capacity_delta,0))
                   ELSE mount_capacity
               END AS effective_capacity,
               CASE
                   WHEN slot_type='weapon_mortar'
                       THEN greatest(
                           coalesce(mount_max_caliber,0),
                           CASE WHEN mortar_modification_installed
                                THEN coalesce(mod_max_caliber,0)
                                ELSE 0 END
                       )
                   ELSE coalesce(mount_max_caliber,0)
               END AS effective_mortar_caliber
          FROM weapon_rows
    )
    SELECT string_agg(
               old_build_id || ':' || slot_type || ':' || slot_index
               || ':' || option_name,
               ', ' ORDER BY old_build_id, slot_type, slot_index
           )
      INTO problem
      FROM checked
     WHERE effective_capacity <= 0
        OR (
            slot_type='weapon_mortar'
            AND (
                option_kind NOT IN ('mortar','mortar_launcher')
                OR (
                    option_kind <> 'mortar_launcher'
                    AND weapon_caliber_inches IS NOT NULL
                    AND effective_mortar_caliber > 0
                    AND weapon_caliber_inches > effective_mortar_caliber
                )
            )
        )
        OR (
            slot_type <> 'weapon_mortar'
            AND option_kind='special_weapon'
            AND (
                slot_type NOT IN ('weapon_front','weapon_rear','weapon_special')
                OR coalesce(special_weapon_capacity,0) <= 0
            )
        )
        OR (
            slot_type <> 'weapon_mortar'
            AND option_kind IN ('mortar','mortar_launcher')
        )
        OR (
            slot_type <> 'weapon_mortar'
            AND coalesce(option_kind,'') <> 'special_weapon'
            AND coalesce(option_kind,'') NOT IN ('mortar','mortar_launcher')
            AND (
                option_kind NOT IN ('cannon','bow_stern')
                OR option_class_rank IS NULL
                OR mount_class_rank IS NULL
                OR option_class_rank > mount_class_rank
            )
        );
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Target weapon compatibility changed for: %', problem;
    END IF;

    -- Aggregate quantity must fit the target ship's effective capacity.
    WITH capacity_rows AS (
        SELECT st.old_build_id, st.slot_type,
               sum(coalesce(st.quantity,1)) AS selected_quantity,
               max(
                   CASE
                       WHEN m.capacity IS NULL THEN 0
                       WHEN b.mortar_modification_installed
                            AND st.slot_type='weapon_mortar'
                           THEN m.capacity + coalesce(mm.mortar_capacity,0)
                       WHEN b.mortar_modification_installed
                            AND st.slot_type IN ('weapon_port','weapon_starboard')
                           THEN greatest(0, m.capacity + coalesce(mm.broadside_capacity_delta,0))
                       ELSE m.capacity
                   END
               ) AS effective_capacity,
               sum(
                   CASE WHEN o.option_kind='special_weapon'
                        THEN coalesce(st.quantity,1) ELSE 0 END
               ) AS selected_special,
               max(coalesce(m.special_weapon_capacity,0)) AS special_capacity
          FROM _rbf_build_slot_stage st
          JOIN _rbf_build_stage b ON b.old_build_id=st.old_build_id
          JOIN _rbf_ship_resolution sm ON sm.source_ship_id=b.source_ship_id
          JOIN _rbf_option_resolution om ON om.source_option_id=st.source_option_id
          JOIN public.build_item_options o ON o.id=om.target_option_id
          LEFT JOIN public.weapon_slot_types wt ON wt.code=st.slot_type
          LEFT JOIN public.ship_weapon_mounts m
            ON m.ship_id=sm.target_ship_id
           AND m.slot_type_id=wt.id
          LEFT JOIN public.ship_mortar_modifications mm
            ON mm.ship_id=sm.target_ship_id
         WHERE left(st.slot_type,7)='weapon_'
         GROUP BY st.old_build_id, st.slot_type
    )
    SELECT string_agg(
               old_build_id || ':' || slot_type
               || ' qty=' || selected_quantity || '/' || effective_capacity
               || ' special=' || selected_special || '/' || special_capacity,
               ', ' ORDER BY old_build_id, slot_type
           )
      INTO problem
      FROM capacity_rows
     WHERE selected_quantity > effective_capacity
        OR selected_special > special_capacity;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Target weapon capacity changed for: %', problem;
    END IF;
END $$;

-- -------------------------------------------------------------------------
-- 6. Target upgrade-slot availability
-- -------------------------------------------------------------------------
DO $$
DECLARE
    problem text;
BEGIN
    WITH base AS (
        SELECT b.old_build_id, s.upgrade_slots,
               least(greatest(s.upgrade_slots,0),4) AS base_slots,
               CASE
                   WHEN b.research_feature_code IS NOT NULL
                        AND s.upgrade_slots > 0
                   THEN least(
                       greatest(coalesce(f.upgrade_slots_granted,0),0),
                       8 - least(greatest(s.upgrade_slots,0),4)
                   )
                   ELSE 0
               END AS research_slots
          FROM _rbf_build_stage b
          JOIN _rbf_ship_resolution sm ON sm.source_ship_id=b.source_ship_id
          JOIN public.ships s ON s.id=sm.target_ship_id
          LEFT JOIN public.build_features f
            ON f.code=b.research_feature_code
    ), pre AS (
        SELECT *,
               least(
                   greatest(upgrade_slots - 5,0),
                   8 - base_slots
               ) AS ship_extra_slots
          FROM base
    ), pre2 AS (
        SELECT *,
               least(8, base_slots + research_slots + ship_extra_slots)
                   AS pre_expansion_slots
          FROM pre
    ), expansion AS (
        SELECT p.old_build_id,
               coalesce(sum(
                   greatest(
                       0,
                       coalesce(ov.effect_value, base_effect.effect_value,0)
                   )
               ) FILTER (
                   WHERE st.slot_type='upgrade'
                     AND st.slot_index <= p.pre_expansion_slots
               ),0) AS expansion_slots
          FROM pre2 p
          LEFT JOIN _rbf_build_slot_stage st ON st.old_build_id=p.old_build_id
          LEFT JOIN _rbf_option_resolution om
            ON om.source_option_id=st.source_option_id
          LEFT JOIN _rbf_build_stage b ON b.old_build_id=p.old_build_id
          LEFT JOIN _rbf_ship_resolution sm ON sm.source_ship_id=b.source_ship_id
          LEFT JOIN public.build_item_effects base_effect
            ON base_effect.option_id=om.target_option_id
           AND base_effect.effect_key='extra_upgrade_slots'
          LEFT JOIN public.ship_upgrade_effect_overrides ov
            ON ov.ship_id=sm.target_ship_id
           AND ov.option_id=om.target_option_id
           AND ov.effect_key='extra_upgrade_slots'
         GROUP BY p.old_build_id
    ), available AS (
        SELECT p.old_build_id,
               least(
                   8,
                   p.base_slots + p.research_slots + p.ship_extra_slots
                   + CASE WHEN p.upgrade_slots > 0
                          THEN least(
                              e.expansion_slots,
                              8 - p.base_slots
                          )
                          ELSE 0 END
               ) AS available_slots
          FROM pre2 p
          JOIN expansion e ON e.old_build_id=p.old_build_id
    )
    SELECT string_agg(
               st.old_build_id || ':slot=' || st.slot_index
               || '/available=' || a.available_slots,
               ', ' ORDER BY st.old_build_id, st.slot_index
           )
      INTO problem
      FROM _rbf_build_slot_stage st
      JOIN available a ON a.old_build_id=st.old_build_id
     WHERE st.slot_type='upgrade'
       AND st.slot_index > a.available_slots;
    IF problem IS NOT NULL THEN
        RAISE EXCEPTION 'Target upgrade-slot availability changed for: %', problem;
    END IF;
END $$;

-- -------------------------------------------------------------------------
-- 7. Import idempotently, never overwrite conflicting current builds
-- -------------------------------------------------------------------------
CREATE TEMP TABLE _rbf_build_map (
    old_build_id integer PRIMARY KEY,
    new_build_id integer NOT NULL,
    inserted boolean NOT NULL
) ON COMMIT DROP;

DO $$
DECLARE
    r record;
    owner_id_value integer;
    ship_id_value integer;
    feature_id_value integer;
    existing_count integer;
    target_build_id integer;
BEGIN
    FOR r IN SELECT * FROM _rbf_build_stage ORDER BY old_build_id LOOP
        SELECT target_user_id
          INTO STRICT owner_id_value
          FROM _rbf_owner_resolution
         WHERE source_username=r.owner_username;

        SELECT target_ship_id
          INTO STRICT ship_id_value
          FROM _rbf_ship_resolution
         WHERE source_ship_id=r.source_ship_id;

        IF r.research_feature_code IS NULL THEN
            feature_id_value := NULL;
        ELSE
            SELECT id INTO STRICT feature_id_value
              FROM public.build_features
             WHERE code=r.research_feature_code;
        END IF;

        SELECT count(*), min(b.id)
          INTO existing_count, target_build_id
          FROM public.builds b
         WHERE b.owner_id IS NOT DISTINCT FROM owner_id_value
           AND b.build_name=r.build_name
           AND b.build_type=r.build_type
           AND b.ship_id=ship_id_value
           AND b.created_at=r.created_at;

        IF existing_count > 1 THEN
            RAISE EXCEPTION
              'Ambiguous existing build match for old build % (%)',
              r.old_build_id, r.build_name;
        END IF;

        IF existing_count = 1 THEN
            IF EXISTS (
                SELECT 1
                  FROM public.builds b
                 WHERE b.id=target_build_id
                   AND (
                       b.is_official_template IS DISTINCT FROM r.is_official_template
                    OR b.sailors IS DISTINCT FROM r.sailors
                    OR b.soldiers IS DISTINCT FROM r.soldiers
                    OR b.musketeers IS DISTINCT FROM r.musketeers
                    OR b.mercenaries IS DISTINCT FROM r.mercenaries
                    OR b.details IS DISTINCT FROM r.details
                    OR b.updated_at IS DISTINCT FROM r.updated_at
                    OR b.mortar_modification_installed
                       IS DISTINCT FROM r.mortar_modification_installed
                    OR b.research_upgrade_feature_id
                       IS DISTINCT FROM feature_id_value
                   )
            ) THEN
                RAISE EXCEPTION
                  'Existing target build differs from backup for old build % (%)',
                  r.old_build_id, r.build_name;
            END IF;

            INSERT INTO _rbf_build_map
            VALUES (r.old_build_id, target_build_id, false);
        ELSE
            INSERT INTO public.builds (
                build_name, build_type, ship_id, owner_id,
                is_official_template, sailors, soldiers, musketeers,
                mercenaries, details, created_at, updated_at,
                mortar_modification_installed, research_upgrade_feature_id
            ) VALUES (
                r.build_name, r.build_type, ship_id_value, owner_id_value,
                r.is_official_template, r.sailors, r.soldiers,
                r.musketeers, r.mercenaries, r.details, r.created_at,
                r.updated_at, r.mortar_modification_installed,
                feature_id_value
            )
            RETURNING id INTO target_build_id;

            INSERT INTO _rbf_build_map
            VALUES (r.old_build_id, target_build_id, true);
        END IF;
    END LOOP;
END $$;

DO $$
DECLARE
    conflict_count integer;
BEGIN
    SELECT count(*)
      INTO conflict_count
      FROM _rbf_build_slot_stage st
      JOIN _rbf_build_map bm ON bm.old_build_id=st.old_build_id
      JOIN _rbf_option_resolution om ON om.source_option_id=st.source_option_id
      JOIN public.build_slots bs
        ON bs.build_id=bm.new_build_id
       AND bs.slot_type=st.slot_type
       AND bs.slot_index=st.slot_index
     WHERE bs.option_id IS DISTINCT FROM om.target_option_id
        OR bs.quantity IS DISTINCT FROM st.quantity;

    IF conflict_count <> 0 THEN
        RAISE EXCEPTION
          'Target contains % conflicting build slot positions; refusing to overwrite them.',
          conflict_count;
    END IF;
END $$;

INSERT INTO public.build_slots (
    build_id, slot_type, slot_index, option_id, quantity, created_at, updated_at
)
SELECT bm.new_build_id, st.slot_type, st.slot_index,
       om.target_option_id, st.quantity, st.created_at, st.updated_at
  FROM _rbf_build_slot_stage st
  JOIN _rbf_build_map bm ON bm.old_build_id=st.old_build_id
  JOIN _rbf_option_resolution om ON om.source_option_id=st.source_option_id
 WHERE NOT EXISTS (
       SELECT 1
         FROM public.build_slots bs
        WHERE bs.build_id=bm.new_build_id
          AND bs.slot_type=st.slot_type
          AND bs.slot_index=st.slot_index
          AND bs.option_id=om.target_option_id
          AND bs.quantity IS NOT DISTINCT FROM st.quantity
 );

INSERT INTO public.build_classifications(build_id, tag)
SELECT bm.new_build_id, st.tag
  FROM _rbf_build_classification_stage st
  JOIN _rbf_build_map bm ON bm.old_build_id=st.old_build_id
 WHERE NOT EXISTS (
       SELECT 1
         FROM public.build_classifications bc
        WHERE bc.build_id=bm.new_build_id
          AND bc.tag=st.tag
 );

-- -------------------------------------------------------------------------
-- 8. Post-import logical verification
-- -------------------------------------------------------------------------
DO $$
DECLARE
    expected_count integer;
    actual_count integer;
BEGIN
    SELECT count(*) INTO expected_count FROM _rbf_build_stage;
    SELECT count(*) INTO actual_count FROM _rbf_build_map;
    IF actual_count <> expected_count THEN
        RAISE EXCEPTION
          'Build mapping verification failed: expected %, got %',
          expected_count, actual_count;
    END IF;

    SELECT count(*) INTO expected_count FROM _rbf_build_slot_stage;
    SELECT count(*)
      INTO actual_count
      FROM _rbf_build_slot_stage st
      JOIN _rbf_build_map bm ON bm.old_build_id=st.old_build_id
      JOIN _rbf_option_resolution om ON om.source_option_id=st.source_option_id
      JOIN public.build_slots bs
        ON bs.build_id=bm.new_build_id
       AND bs.slot_type=st.slot_type
       AND bs.slot_index=st.slot_index
       AND bs.option_id=om.target_option_id
       AND bs.quantity IS NOT DISTINCT FROM st.quantity;
    IF actual_count <> expected_count THEN
        RAISE EXCEPTION
          'Build slot verification failed: expected %, got %',
          expected_count, actual_count;
    END IF;

    SELECT count(*) INTO expected_count FROM _rbf_build_classification_stage;
    SELECT count(*)
      INTO actual_count
      FROM _rbf_build_classification_stage st
      JOIN _rbf_build_map bm ON bm.old_build_id=st.old_build_id
      JOIN public.build_classifications bc
        ON bc.build_id=bm.new_build_id
       AND bc.tag=st.tag;
    IF actual_count <> expected_count THEN
        RAISE EXCEPTION
          'Build classification verification failed: expected %, got %',
          expected_count, actual_count;
    END IF;
END $$;

SELECT count(*) FILTER (WHERE inserted) AS builds_inserted,
       count(*) FILTER (WHERE NOT inserted) AS builds_already_present,
       count(*) AS builds_verified
  FROM _rbf_build_map;

SELECT count(*) AS slots_verified FROM _rbf_build_slot_stage;
SELECT count(*) AS classifications_verified
  FROM _rbf_build_classification_stage;

\if :dry_run
  \echo 'DRY RUN successful; rolling back all changes.'
  ROLLBACK;
\else
  COMMIT;
  \echo 'Build-only restore committed successfully.'
\endif
