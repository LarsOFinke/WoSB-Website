SHELL := /usr/bin/env bash

.PHONY: setup setup-core up down restart status logs update backup backup-db backup-files smoke doctor lint config

setup:
	sudo ../setup.sh --profile full

setup-core:
	sudo ../setup.sh --profile core

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

backup:
	sudo ./scripts/backup/backup-all.sh

backup-db:
	./scripts/backup/backup-postgres.sh

backup-files:
	./scripts/backup/backup-data.sh

smoke:
	./scripts/checks/smoke-test.sh

doctor:
	./scripts/checks/doctor.sh

lint:
	./scripts/checks/lint.sh

config:
	@source scripts/lib/docker.sh && bw_compose_with_profiles config
