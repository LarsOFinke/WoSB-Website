SHELL := /usr/bin/env bash

.PHONY: dev-backend dev-frontend test test-full test-recovery test-recovery-matrix lint css-audit security-audit build validate clean clean-all check-tree build-recovery-linux clear-pycache setup-pi doctor infra-up infra-down infra-status infra-logs infra-backup infra-update

dev-backend:
	cd backend && rbf-dev

dev-frontend:
	cd frontend && npm run dev

test:
	bash ./scripts/test.sh quick

test-full:
	bash ./scripts/test.sh full

test-recovery:
	python -m pytest -q -p no:cacheprovider tools/recovery-tool/tests tests/recovery

test-recovery-matrix:
	@test -n "$$RECOVERY_MATRIX_DATABASE_URL" || { echo "RECOVERY_MATRIX_DATABASE_URL fehlt" >&2; exit 2; }
	python scripts/test_recovery_matrix.py

lint:
	cd backend && ruff check --no-cache src tests

css-audit:
	python scripts/audit_css.py

security-audit:
	python scripts/security_audit.py

validate:
	bash ./scripts/test.sh full

build:
	cd frontend && npm run build

clean:
	bash ./scripts/clean_repository.sh

clean-all:
	bash ./scripts/clean_repository.sh --all

check-tree:
	python ./scripts/check_repository.py --strict-tree

build-recovery-linux:
	cd tools/linux/recovery-tool && ./Build-RbfRecoveryTool.sh

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
