#!/usr/bin/env python3
"""Fail-closed repository invariants for the Spring-only application."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def require(condition: bool, message: str) -> None:
    if not condition: raise SystemExit(f"[repository] {message}")

def text(path: str) -> str:
    target=ROOT/path; require(target.is_file(),f"missing {path}"); return target.read_text(encoding='utf-8')

parser=argparse.ArgumentParser(); parser.add_argument('--strict-tree',action='store_true'); args=parser.parse_args()
version=text('VERSION').strip(); require(re.fullmatch(r'\d+\.\d+\.\d+',version) is not None,'VERSION must be SemVer')
require(f'<version>{version}</version>' in text('spring-api/pom.xml'),'Maven project version differs from VERSION')
require(json.loads(text('frontend/package.json'))['version']==version,'frontend version differs from VERSION')
require(not (ROOT/'backend').exists(),'Python backend directory must not exist')
for path in ('spring-api/src/main/resources/db/migration/V1__current_schema_baseline.sql','spring-api/src/main/resources/application.yml','infrastructure/compose.yml','infrastructure/compose.release.yml','scripts/package_deployment_artifact.py','contracts/api-contract.json','contracts/build-stat-catalog.json','contracts/webhook-events.json'):
    text(path)

contract=json.loads(text('contracts/api-contract.json'))
operations=[]
for item in contract.get('paths',{}).values():
    for operation in item.values():
        if isinstance(operation,dict) and operation.get('operationId'): operations.append(operation['operationId'])
require(len(operations)==177 and len(set(operations))==177,f'API contract must expose 177 unique operations, found {len(operations)}/{len(set(operations))}')
require(len(list((ROOT/'spring-api/src/main/java/eu/royalblackwater/api/contract').glob('*.java')))==len(contract['components']['schemas']),'generated Java contract count is stale')

compose=text('infrastructure/compose.yml')
for service in ('postgres:','api:','gateway:'): require(f'  {service}' in compose,f'missing compose service {service[:-1]}')
for forbidden in ('secure-api:','migrate:','seed:','FASTAPI_INTERNAL_URL','AUTO_SEED','RBF_SECURE_API_IMAGE'): require(forbidden not in compose,f'legacy compose token remains: {forbidden}')
require('flyway-core' in text('spring-api/pom.xml') and 'mapstruct' in text('spring-api/pom.xml'),'Flyway and MapStruct are mandatory')
require('ddl-auto: validate' in text('spring-api/src/main/resources/application.yml'),'Hibernate must validate rather than mutate schema')

allowed_legacy={
    ROOT/'infrastructure/scripts/migration/verify-alembic-head.sql',
    ROOT/'infrastructure/scripts/migration/adopt-flyway.sql',
    ROOT/'infrastructure/scripts/lib/docker.sh',
}
scan_exclusions={
    ROOT/'CHANGELOG.md',
    ROOT/'scripts/check_repository.py',
    ROOT/'scripts/audit_spring_backend.py',
    ROOT/'scripts/test-infrastructure.sh',
}
for path in ROOT.rglob('*'):
    if not path.is_file() or any(part in {'.git','node_modules','target','dist','release'} for part in path.parts): continue
    if path in scan_exclusions or 'audits' in path.parts: continue
    if path in allowed_legacy or path.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.ico','.zip','.gz','.age','.woff','.woff2'}: continue
    source=path.read_text(encoding='utf-8',errors='ignore').lower()
    for forbidden in ('fastapi','uvicorn','rbf-seed','secure-api'):
        require(forbidden not in source,f'legacy runtime token {forbidden!r} in {path.relative_to(ROOT)}')
    if 'alembic' in source:
        require(path in allowed_legacy,f'Alembic reference outside one-time adoption gate: {path.relative_to(ROOT)}')

for path in (ROOT/'spring-api/src/main/java').rglob('*.java'):
    require(len(path.read_text(encoding='utf-8').splitlines())<=420,f'Java file exceeds 420 lines: {path.relative_to(ROOT)}')
for migration in (ROOT/'spring-api/src/main/resources/db/migration').glob('*.sql'):
    require(re.fullmatch(r'V\d+__[A-Za-z0-9_]+\.sql',migration.name) is not None,f'invalid Flyway migration name: {migration.name}')

subprocess.run([sys.executable,str(ROOT/'scripts/audit_spring_backend.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/migration/generate_build_stat_catalog.py'),'--check'],check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/sync_webhook_templates.py'),'--check'],check=True)
if args.strict_tree:
    forbidden_names={'.env','.DS_Store'}
    for path in ROOT.rglob('*'):
        relative=path.relative_to(ROOT)
        require(path.name not in forbidden_names or relative.as_posix() in {'frontend/.env.example','infrastructure/.env.example'},f'untracked local file: {relative}')
        require(path.name!='__pycache__' and path.suffix!='.pyc',f'Python cache artifact: {relative}')
        require(not any(part in {'node_modules','target','dist','.pytest_cache','.ruff_cache','.mypy_cache'} for part in relative.parts),f'build/cache directory committed: {relative}')
print(f'[repository] OK: Spring-only, {len(operations)} operations, version {version}')
