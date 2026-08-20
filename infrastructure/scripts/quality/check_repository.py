#!/usr/bin/env python3
"""Fail-closed repository invariants for the Spring-only application."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def require(condition: bool, message: str) -> None:
    if not condition: raise SystemExit(f"[repository] {message}")

def text(path: str) -> str:
    target=ROOT/path; require(target.is_file(),f"missing {path}"); return target.read_text(encoding='utf-8')

parser=argparse.ArgumentParser(); parser.add_argument('--strict-tree',action='store_true'); args=parser.parse_args()
version=text('VERSION').strip(); require(re.fullmatch(r'\d+\.\d+\.\d+',version) is not None,'VERSION must be SemVer')
require(f'<version>{version}</version>' in text('spring-api/pom.xml'),'Maven project version differs from VERSION')
require(json.loads(text('frontend/package.json'))['version']==version,'frontend version differs from VERSION')
require(not (ROOT/'backend').exists(),'Python backend directory must not exist')
require(not (ROOT/'scripts').exists(),'top-level scripts directory must not be recreated')
root_shell_scripts={path.name for path in ROOT.glob('*.sh')}
require(root_shell_scripts=={'deploy.sh','update.sh'},
        f'root shell entrypoints must be deploy.sh/update.sh, found {sorted(root_shell_scripts)}')
for path in ('spring-api/src/main/resources/db/migration/V1__current_schema_baseline.sql','spring-api/src/main/resources/application.yml','infrastructure/compose.yml','infrastructure/compose.release.yml','infrastructure/scripts/release/package_deployment_artifact.py','openapi/source/root.json','openapi/openapi.json','spring-api/src/main/reference/webhook-events.json'):
    text(path)
require((ROOT/'openapi/source/operations').is_dir(),'missing modular OpenAPI operations')
require((ROOT/'openapi/source/schemas').is_dir(),'missing modular OpenAPI schemas')
require((ROOT/'spring-api/src/main/reference/build-stats').is_dir(),'missing modular build-stat catalog')
require(not (ROOT/'spring-api/src/main/reference/build-stat-catalog.json').exists(),
        'retired build-stat JSON monolith must not return')
require(not any((ROOT/'spring-api/src/main/resources/seed/builds/options').glob('*.json')),
        'build-option seed monoliths must not return')
require(not any((ROOT/'spring-api/src/main/resources/seed/ships/rates').glob('*.json')),
        'ship-rate seed monoliths must not return')
subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/generation/assemble_openapi.py'),'--check'],check=True)

contract=json.loads(text('openapi/openapi.json'))
require(contract.get('info',{}).get('version')==version,'OpenAPI contract version differs from VERSION')
schemas=contract.get('components',{}).get('schemas',{})
require('ApiError' in schemas,'API contract must define the Spring ApiError response schema')
require('HTTPValidationError' not in schemas and 'ValidationError' not in schemas,
        'retired Python validation error schemas must not return to the API contract')

java_keywords={"abstract","assert","boolean","break","byte","case","catch","char","class","const","continue","default","do","double","else","enum","extends","final","finally","float","for","goto","if","implements","import","instanceof","int","interface","long","native","new","package","private","protected","public","return","short","static","strictfp","super","switch","synchronized","this","throw","throws","transient","try","void","volatile","while","record","sealed","permits","yield","var","null","true","false"}
for schema_name,schema in schemas.items():
    for wire_name in schema.get('properties',{}):
        if wire_name not in java_keywords: continue
        generated=text(f'spring-api/src/main/java/eu/royalblackwater/api/dto/{schema_name}.java')
        require(f'@JsonProperty("{wire_name}")' in generated,
                f'generated DTO {schema_name} must preserve reserved wire property {wire_name!r}')

def response_schema_ref(operation: dict, status: str) -> str | None:
    return (operation.get('responses',{}).get(status,{})
            .get('content',{}).get('application/json',{}).get('schema',{}).get('$ref'))

login_operation=contract.get('paths',{}).get('/api/auth/login',{}).get('post',{})
require(login_operation.get('requestBody',{}).get('content',{}).get('application/json',{}).get('schema',{}).get('$ref')
        == '#/components/schemas/LoginRequest','login request contract must use LoginRequest')
require(response_schema_ref(login_operation,'200')=='#/components/schemas/LoginResponse',
        'login success contract must use LoginResponse')
require(response_schema_ref(login_operation,'400')=='#/components/schemas/ApiError',
        'login validation failures must be documented as HTTP 400 ApiError')
require(response_schema_ref(login_operation,'401')=='#/components/schemas/ApiError',
        'invalid login credentials must be documented as HTTP 401 ApiError')

domain_422={
    ('/api/profile','put'),
    ('/api/privacy/contact','post'),
    ('/api/privacy/cookie-consent','post'),
    ('/api/privacy/requests','post'),
    ('/api/admin/privacy-requests/{request_id}','put'),
    ('/api/admin/privacy-requests/contacts/{request_id}','put'),
}
actual_422=set()
for api_path,item in contract.get('paths',{}).items():
    for method,operation in item.items():
        if not isinstance(operation,dict): continue
        if '422' in operation.get('responses',{}):
            require(response_schema_ref(operation,'422')=='#/components/schemas/ApiError',
                    f'{method.upper()} {api_path} must use ApiError for HTTP 422')
            actual_422.add((api_path,method))
require(actual_422==domain_422,
        f'HTTP 422 contract drift: expected {sorted(domain_422)}, found {sorted(actual_422)}')
operations=[]
for item in contract.get('paths',{}).values():
    for operation in item.values():
        if isinstance(operation,dict) and operation.get('operationId'): operations.append(operation['operationId'])
require(len(operations)==194 and len(set(operations))==194,f'API contract must expose 194 unique operations, found {len(operations)}/{len(set(operations))}')
require(len(list((ROOT/'spring-api/src/main/java/eu/royalblackwater/api/dto').glob('*.java')))==len(contract['components']['schemas']),'generated Java DTO count is stale')
require(not (ROOT/'spring-api/src/main/java/eu/royalblackwater/api/contract').exists(),'obsolete generated contract layer remains')

compose=text('infrastructure/compose.yml')
for service in ('postgres:','api:','gateway:'): require(f'  {service}' in compose,f'missing compose service {service[:-1]}')
for forbidden in ('secure-api:','migrate:','seed:','FASTAPI_INTERNAL_URL','AUTO_SEED','RBF_SECURE_API_IMAGE'): require(forbidden not in compose,f'legacy compose token remains: {forbidden}')
require('spring-boot-starter-flyway' in text('spring-api/pom.xml') and 'mapstruct' in text('spring-api/pom.xml'),'Flyway and MapStruct are mandatory')
require('ddl-auto: validate' in text('spring-api/src/main/resources/application.yml'),'Hibernate must validate rather than mutate schema')
ci_requirements=text('requirements-ci.txt')
require(re.fullmatch(r'# Python dependencies used only by repository and recovery tests\.\npytest==\d+\.\d+\.\d+\n',ci_requirements) is not None,
        'CI Python test dependencies must remain minimal and exactly pinned')
for workflow_path in ('.github/workflows/ci.yml','.github/workflows/release.yml'):
    workflow=text(workflow_path)
    require('actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1' in workflow,
            f'{workflow_path} must configure the pinned Python runtime action')
    require('python -m pip install --disable-pip-version-check -r requirements-ci.txt' in workflow,
            f'{workflow_path} must install the pinned Python test dependencies')

allowed_legacy={
    ROOT/'infrastructure/scripts/migration/verify-alembic-head.sql',
    ROOT/'infrastructure/scripts/migration/adopt-flyway.sql',
    ROOT/'infrastructure/scripts/lib/docker.sh',
}
scan_exclusions={
    ROOT/'CHANGELOG.md',
    ROOT/'infrastructure/scripts/quality/check_repository.py',
    ROOT/'infrastructure/scripts/quality/audit_spring_backend.py',
    ROOT/'infrastructure/scripts/quality/tests/infrastructure.sh',
}
repository_result=subprocess.run(
    ['git','-C',str(ROOT),'ls-files','--cached','--others','--exclude-standard','-z'],
    check=True,capture_output=True,text=True,
)
repository_files=[Path(raw) for raw in repository_result.stdout.split('\0') if raw]
for relative in repository_files:
    path=ROOT/relative
    if not path.is_file() or path.suffix == '.pyc' or any(part in {'node_modules','target','dist','release','__pycache__'} for part in relative.parts): continue
    if relative.parts and relative.parts[0] == 'patches': continue
    if path in scan_exclusions: continue
    if path in allowed_legacy or path.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.ico','.zip','.gz','.age','.woff','.woff2'}: continue
    source=path.read_text(encoding='utf-8',errors='ignore').lower()
    for forbidden in ('fastapi','uvicorn','rbf-seed','secure-api'):
        require(forbidden not in source,f'legacy runtime token {forbidden!r} in {path.relative_to(ROOT)}')
    if 'alembic' in source:
        require(path in allowed_legacy,f'Alembic reference outside one-time adoption gate: {path.relative_to(ROOT)}')

for path in (ROOT/'spring-api/src/main/java').rglob('*.java'):
    require(len(path.read_text(encoding='utf-8').splitlines())<=420,f'Java file exceeds 420 lines: {path.relative_to(ROOT)}')
frontend_source=ROOT/'frontend/src'
declarative_javascript_files={frontend_source/'locales/autoLocalizationCatalog.js'}
declarative_javascript_roots=(frontend_source/'locales/messages',)
for path in (*frontend_source.rglob('*.js'),*frontend_source.rglob('*.mjs')):
    if path in declarative_javascript_files or any(root in path.parents for root in declarative_javascript_roots): continue
    require(len(path.read_text(encoding='utf-8').splitlines())<=420,f'JavaScript file exceeds 420 lines: {path.relative_to(ROOT)}')
for path in frontend_source.rglob('*.vue'):
    require(len(path.read_text(encoding='utf-8').splitlines())<=420,
            f'Vue component exceeds 420 lines: {path.relative_to(ROOT)}')
for migration in (ROOT/'spring-api/src/main/resources/db/migration').glob('*.sql'):
    require(re.fullmatch(r'[BV]\d+__[A-Za-z0-9_]+\.sql',migration.name) is not None,f'invalid Flyway migration name: {migration.name}')

# Hand-maintained JSON follows the same readability ceiling as executable source.
# Generated compatibility/lock artifacts are intentionally excluded.
for source_root in (ROOT/'openapi/source', ROOT/'spring-api/src/main/reference',
                    ROOT/'spring-api/src/main/resources/seed', ROOT/'frontend/tests/fixtures'):
    for path in source_root.rglob('*.json'):
        require(len(path.read_text(encoding='utf-8').splitlines()) <= 420,
                f'hand-maintained JSON exceeds 420 lines: {path.relative_to(ROOT)}')

subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/quality/audit_controller_contract.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/quality/audit_authorization_policy.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/quality/audit_spring_backend.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/quality/audit_sql_runtime.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/generation/generate_build_stat_catalog.py'),'--check'],check=True)
subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/generation/generate_modular_flyway_baseline.py'),'--check'],check=True)
subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/generation/generate_api_reference.py'),'--check'],check=True)
subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/generation/generate_api_dtos.py'),'--check'],check=True)
subprocess.run([sys.executable,str(ROOT/'infrastructure/scripts/generation/sync_webhook_templates.py'),'--check'],check=True)
if args.strict_tree:
    forbidden_names={'.env','.DS_Store'}
    for relative in repository_files:
        path=ROOT/relative
        require(path.name not in forbidden_names or relative.as_posix() in {'frontend/.env.example','infrastructure/.env.example'},f'untracked local file: {relative}')
        require(path.name!='__pycache__' and path.suffix!='.pyc',f'Python cache artifact: {relative}')
        require(not any(part in {'node_modules','target','dist','.pytest_cache','.ruff_cache','.mypy_cache'} for part in relative.parts),f'build/cache directory committed: {relative}')
print(f'[repository] OK: Spring-only, {len(operations)} operations, version {version}')
