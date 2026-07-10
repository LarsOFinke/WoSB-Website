SHELL := /usr/bin/env bash

.PHONY: dev-backend dev-frontend test build setup-pi infra-up infra-down infra-status infra-logs infra-backup infra-update

dev-backend:
	cd backend && rbf-dev

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest -q
	cd frontend && npm run check:locales

build:
	cd frontend && npm run build

setup-pi:
	sudo ./infrastructure/setup.sh --profile full

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
	$(MAKE) -C infrastructure update
