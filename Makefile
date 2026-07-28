SHELL := /usr/bin/env bash

.PHONY: dev-backend dev-frontend test test-full lint css-audit build validate clear-pycache setup-pi doctor infra-up infra-down infra-status infra-logs infra-backup infra-update

dev-backend:
	cd backend && rbf-dev

dev-frontend:
	cd frontend && npm run dev

test:
	bash ./scripts/test.sh quick

test-full:
	bash ./scripts/test.sh full

lint:
	cd backend && ruff check --no-cache src tests

css-audit:
	python scripts/audit_css.py

validate:
	bash ./scripts/test.sh full

build:
	cd frontend && npm run build

clear-pycache:
	bash ./backend/scripts/clear-pycache.sh

setup-pi:
	sudo ./infrastructure/setup.sh --profile full

doctor:
	sudo ./infrastructure/scripts/checks/doctor.sh

infra-up:
	$(MAKE) -C infrastructure up

infra-down:
	$(MAKE) -C infrastructure down

infra-status:
	$(MAKE) -C infrastructure status

infra-logs:
	$(MAKE) -C infrastructure logs

infra-backup:
	$(MAKE) -C infrastructure backup

infra-update:
	sudo ./update.sh
