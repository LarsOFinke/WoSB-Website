-- One-time, reviewed adoption of a database at Alembic head 0025 by Flyway.
-- verify-alembic-head.sql MUST run successfully in the same maintenance window first.
BEGIN;
SELECT pg_advisory_xact_lock(hashtext('rbf-flyway-adoption'));
DO $$
BEGIN
    IF to_regclass(current_schema() || '.flyway_schema_history') IS NOT NULL THEN
        RAISE EXCEPTION 'flyway_schema_history already exists';
    END IF;
    IF to_regclass(current_schema() || '.alembic_version') IS NULL THEN
        RAISE EXCEPTION 'alembic_version is absent';
    END IF;
END $$;
CREATE TABLE flyway_schema_history (
    installed_rank integer NOT NULL,
    version varchar(50),
    description varchar(200) NOT NULL,
    type varchar(20) NOT NULL,
    script varchar(1000) NOT NULL,
    checksum integer,
    installed_by varchar(100) NOT NULL,
    installed_on timestamp without time zone NOT NULL DEFAULT now(),
    execution_time integer NOT NULL,
    success boolean NOT NULL,
    CONSTRAINT flyway_schema_history_pk PRIMARY KEY (installed_rank)
);
CREATE INDEX flyway_schema_history_s_idx ON flyway_schema_history (success);
INSERT INTO flyway_schema_history(
    installed_rank,version,description,type,script,checksum,installed_by,execution_time,success)
VALUES (1,'1','reviewed Alembic 0025 schema','BASELINE','<< Flyway Baseline >>',NULL,current_user,0,true);
DROP TABLE alembic_version;
COMMIT;
