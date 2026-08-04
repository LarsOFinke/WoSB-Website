SHELL := /usr/bin/env bash
.PHONY: dev-api dev-frontend test test-full spring-test frontend-test lint css-audit security-audit build validate clean clean-all check-tree setup-pi doctor infra-up infra-down infra-status infra-logs infra-backup infra-update package-release

dev-api:
	mvn -f spring-api/pom.xml spring-boot:run

dev-frontend:
	cd frontend && npm run dev

test:
	bash ./scripts/test.sh quick

test-full validate:
	bash ./scripts/test.sh full

spring-test:
	mvn -f spring-api/pom.xml --batch-mode --no-transfer-progress verify

frontend-test:
	cd frontend && npm run test:ci

lint:
	python scripts/check_repository.py
	bash scripts/test-infrastructure.sh

css-audit:
	python scripts/audit_css.py

security-audit:
	python scripts/security_audit.py

build:
	mvn -f spring-api/pom.xml --batch-mode --no-transfer-progress package
	cd frontend && npm run build

clean:
	bash ./scripts/clean_repository.sh

clean-all:
	bash ./scripts/clean_repository.sh --all

check-tree:
	python ./scripts/check_repository.py --strict-tree

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

package-release:
	bash infrastructure/scripts/release/build-artifact.sh
