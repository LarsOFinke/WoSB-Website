SHELL := /usr/bin/env bash
.PHONY: dev-api dev-frontend test test-full spring-test frontend-test lint sql-audit css-audit security-audit build validate clean clean-all check-tree setup-pi doctor infra-up infra-down infra-status infra-logs infra-backup infra-update package-release

dev-api:
	mvn -f spring-api/pom.xml spring-boot:run

dev-frontend:
	cd frontend && npm run dev

test:
	bash ./infrastructure/scripts/quality/validate.sh quick

test-full validate:
	bash ./infrastructure/scripts/quality/validate.sh full

spring-test:
	mvn -f spring-api/pom.xml --batch-mode --no-transfer-progress verify

frontend-test:
	cd frontend && npm run test:ci

lint:
	python3 infrastructure/scripts/quality/check_repository.py
	python3 infrastructure/scripts/quality/check_documentation.py
	bash infrastructure/scripts/quality/tests/infrastructure.sh
	bash infrastructure/scripts/quality/tests/tls-environment-safety.sh

sql-audit:
	python3 infrastructure/scripts/quality/audit_sql_runtime.py

css-audit:
	python3 infrastructure/scripts/quality/audit_css.py

security-audit:
	python3 infrastructure/scripts/quality/security_audit.py

build:
	mvn -f spring-api/pom.xml --batch-mode --no-transfer-progress package
	cd frontend && npm run build

clean:
	bash ./infrastructure/scripts/quality/clean_repository.sh

clean-all:
	bash ./infrastructure/scripts/quality/clean_repository.sh --all

check-tree:
	python3 ./infrastructure/scripts/quality/check_repository.py --strict-tree

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
	bash ./infrastructure/scripts/release/build-artifact.sh
