SHELL := /usr/bin/env bash

.PHONY: setup setup-core up down restart status logs update backup backup-db backup-files smoke config

setup:
	./setup.sh --profile full

setup-core:
	./setup.sh --profile core

up:
	./scripts/services/start.sh

down:
	./scripts/services/stop.sh

restart:
	./scripts/services/restart.sh

status:
	./scripts/services/status.sh

logs:
	./scripts/services/logs.sh

update:
	sudo ../update.sh

backup: backup-db backup-files

backup-db:
	./scripts/backup/backup-postgres.sh

backup-files:
	./scripts/backup/backup-data.sh

smoke:
	./scripts/checks/smoke-test.sh

config:
	@source scripts/lib/docker.sh && bw_compose_with_profiles config
