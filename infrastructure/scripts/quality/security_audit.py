#!/usr/bin/env python3
"""Static, fail-closed security invariants for application and deployment boundaries."""
from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def require(value: bool,message: str)->None:
    if not value: raise SystemExit(f'[security] {message}')
def read(path: str)->str:
    target=ROOT/path; require(target.is_file(),f'missing {path}'); return target.read_text(encoding='utf-8')

security=read('spring-api/src/main/java/eu/royalblackwater/api/config/SecurityConfiguration.java')
for contract in ('.csrf(csrf ->','CookieCsrfTokenRepository','withHttpOnlyFalse()', '.requestMatchers("/api/admin/**").hasAuthority("ROLE_ADMIN")','.requestMatchers("/api/**").authenticated()','.anyRequest().denyAll()','SessionCreationPolicy.STATELESS','setAllowCredentials(true)'):
    require(contract in security,f'missing Spring Security contract: {contract}')
require('csrf.disable' not in security,'CSRF must not be disabled')
require('"*"' not in re.search(r'CorsConfigurationSource[\s\S]+?return source;',security).group(0),'credentialed CORS must not allow wildcard origins')
app=read('spring-api/src/main/resources/application.yml')
for contract in ('include-message: never','show-details: never','open-in-view: false','ddl-auto: validate','clean-disabled: true','fail-on-unknown-properties: true','fail_on_pagination_over_collection_fetch: true'):
    require(contract in app,f'missing production setting: {contract}')
require('baseline-on-migrate: ${FLYWAY_BASELINE_ON_MIGRATE:false}' in app,'unsafe automatic Flyway baseline default')
password=read('spring-api/src/main/java/eu/royalblackwater/api/security/service/PasswordHasher.java')
require('ITERATIONS = 600_000' in password and 'PBKDF2WithHmacSHA256' in password,'password hashing policy regressed')
session=read('spring-api/src/main/java/eu/royalblackwater/api/security/service/SessionTokenService.java')
require('new byte[32]' in session and 'SHA-256' in session,'session token entropy/hash policy regressed')
auth=read('spring-api/src/main/java/eu/royalblackwater/api/account/controller/AuthController.java')
for contract in ('.httpOnly(true)','.secure(session.secure())','.sameSite(session.sameSite())','.maxAge(session.ttl())'):
    require(contract in auth,f'session cookie contract missing: {contract}')
secret=read('spring-api/src/main/java/eu/royalblackwater/api/security/service/FernetSecretBox.java')
require('At least one application encryption key is required' in secret,'secret key must be mandatory')
for forbidden in ('derivedKey(', 'databaseUrl', 'AES/ECB', 'Cipher.getInstance("AES")'):
    require(forbidden not in secret,f'insecure secret-box fallback remains: {forbidden}')

java_root=ROOT/'spring-api/src/main/java'
all_java='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in java_root.rglob('*.java'))
for forbidden in ('Runtime.getRuntime().exec','ProcessBuilder(', 'TrustAll', 'HostnameVerifier', 'setFollowRedirects(true)', 'FetchType.EAGER'):
    require(forbidden not in all_java,f'forbidden Java security pattern: {forbidden}')
require('SKIP LOCKED' in all_java.upper(),'persistent delivery workers must claim rows without duplicate work')

for compose_path in ('infrastructure/compose.yml','infrastructure/compose.release.yml'):
    compose=read(compose_path)
    sections={}
    for service in ('postgres','schema','api','gateway'):
        match=re.search(rf'(?ms)^  {re.escape(service)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)', compose)
        require(match is not None,f'{compose_path}: missing service {service}')
        sections[service]=match.group(1)
        for contract in ('read_only: true','no-new-privileges:true','cap_drop: [ALL]','mem_limit:','cpus:','pids_limit:'):
            require(contract in sections[service],f'{compose_path}: {service} lacks {contract}')
        require('env_file:' not in sections[service],f'{compose_path}: {service} receives the complete environment file')
    require('SPRING_FLYWAY_ENABLED: "false"' in sections['api'],'runtime API may not own schema migrations')
    require('api_app_password' in sections['api'],'runtime API lacks isolated database secret')
    require('schema_owner_password' in sections['schema'],'schema job lacks owner-only credential')
    require('POSTGRES_PASSWORD_FILE' in sections['postgres'],'PostgreSQL password must use a mounted secret')
require('127.0.0.1:${POSTGRES_LOCAL_PORT' in read('infrastructure/compose.yml'),'development PostgreSQL may only bind loopback')
require('ports:' not in re.search(r'(?ms)^  postgres:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n)',read('infrastructure/compose.release.yml')).group(1),'release PostgreSQL may not publish a port')
host_approval=read('infrastructure/scripts/services/host-operation-approval.py')
for contract in ('O_NOFOLLOW','metadata.st_uid != 0','hmac.compare_digest','path.unlink(missing_ok=True)'):
    require(contract in host_approval,f'host-operation approval lost fail-closed contract: {contract}')
installer=read('infrastructure/scripts/release/verify-artifact.py')
for contract in ('Links and special files are forbidden','Artifact checksum mismatch','Artifact inventory mismatch','path.is_absolute()','".." in path.parts'):
    require(contract in installer,f'artifact verifier lost safety contract: {contract}')
recovery=read('infrastructure/scripts/backup/recovery_bundle.py')
for contract in ('Links and special entries are forbidden','Checksum mismatch','Inventory mismatch','path.is_absolute()'):
    require(contract in recovery,f'recovery verifier lost safety contract: {contract}')
nginx=read('infrastructure/nginx/default.conf')
for header in ('Content-Security-Policy','X-Content-Type-Options','Referrer-Policy'):
    require(header in read('infrastructure/nginx/security-headers.conf'),f'missing gateway header {header}')
require('proxy_set_header X-Forwarded-For $remote_addr;' in nginx,'untrusted forwarded chain may not be propagated')
require('limit_req_zone $binary_remote_addr zone=file_content:10m rate=600r/m;' in nginx,
        'build/master-data media must have a dedicated bounded download rate')
media_location=re.search(r'location ~ \^/api/files/\[0-9\]\+/content\$ \{([\s\S]*?)\n    \}', nginx)
require(media_location is not None,'dedicated file-content gateway location missing')
media_block=media_location.group(1)
require('limit_req zone=file_content burst=300 nodelay;' in media_block,
        'file-content route must use the reviewed media limiter')
require('limit_req zone=api_general' not in media_block,
        'file-content fetches must not consume the interactive API rate budget')
require('limit_conn connections_per_ip 20;' in media_block,
        'file-content route must retain a per-IP concurrency bound')

printout_queries=read('spring-api/src/main/java/eu/royalblackwater/api/builds/repository/queries/BuildPrintoutQueries.java')
printout_service=read('spring-api/src/main/java/eu/royalblackwater/api/builds/service/BuildPrintoutService.java')
file_queries=read('spring-api/src/main/java/eu/royalblackwater/api/files/repository/queries/FileAssetQueries.java')
printout_migration=read('spring-api/src/main/resources/db/migration/V8__build_printout_cache.sql')
require('for update' in printout_queries.lower(),
        'build printout cache writes must serialize on the build row')
require('printout_source_updated_at=:sourceUpdatedAt' in printout_queries and
        'updated_at=:now' not in printout_queries.replace('printout_updated_at=:now', ''),
        'derived printout cache writes must not mutate the business build revision')
require('build-" + buildId + "-" + checksum + ".png"' in printout_service,
        'build printouts must use checksum-versioned files for transaction-safe replacement')
require('cache_key=' in printout_service and 'cacheKey.equals(RowValues.string(build, "printout_cache_key"))' in printout_service,
        'build printout downloads must bind the HTTP URL to the current server cache key')
require('sum(printout_size_bytes)' in file_queries and 'sum(size_bytes)' in file_queries,
        'ordinary uploads and shared build printouts must consume one global storage budget')
for column in ('printout_cache_key', 'printout_source_updated_at'):
    require(column in printout_migration, f'build printout cache migration missing {column}')
pom=read('spring-api/pom.xml')
require('<tomcat.version>11.0.24</tomcat.version>' in pom,
        'embedded Tomcat must retain the reviewed security update')
require('<log4j2.version>2.25.5</log4j2.version>' in pom,
        'Log4j API must retain the reviewed security update')
require('<postgresql.version>42.7.12</postgresql.version>' in pom,
        'PostgreSQL JDBC must retain the reviewed security update')
for dockerfile in ('spring-api/Dockerfile','infrastructure/docker/api-runtime.Dockerfile',
                   'infrastructure/docker/frontend.Dockerfile','infrastructure/docker/gateway-runtime.Dockerfile'):
    require('apk upgrade --no-cache' in read(dockerfile),
            f'{dockerfile} must apply Alpine security updates during the image build')
security_workflow=read('.github/workflows/security.yml')
require(not (ROOT/'.github/dependabot.yml').exists(),
        'automated dependency version-update pull requests must remain disabled')
require('org.owasp:dependency-check-maven:12.2.2:check' in security_workflow,
        'OWASP dependency-check must use the reviewed pinned version')
require('NVD_API_KEY: ${{ secrets.NVD_API_KEY }}' in security_workflow and
        'if [[ -n "$NVD_API_KEY" ]]' in security_workflow,
        'OWASP dependency-check must consume only a non-empty GitHub NVD secret')
require('nvdApiKeyEnvironmentVariable=NVD_API_KEY' in security_workflow,
        'OWASP dependency-check must receive its optional NVD key through an environment variable')
require("schedule: [{cron: '17 4 * * *'}]" in security_workflow,
        'dependency vulnerability scan must run daily')
require('actions/cache@5a3ec84eff668545956fd18022155c47e93e2684' in security_workflow and
        '~/.m2/repository/org/owasp/dependency-check-data' in security_workflow,
        'OWASP dependency-check data cache must be restored with the reviewed pinned cache action')
require('org.owasp:dependency-check-maven:12.2.2:update-only' in security_workflow and
        '-DnvdValidForHours=0' in security_workflow,
        'daily security workflow must refresh the vulnerability cache before analysis')
require('check_dependency_suppressions.py' in security_workflow,
        'temporary dependency suppressions must be checked against NVD before scanning')
for contract in ('-DautoUpdate=false', '-DfailBuildOnCVSS=7',
                 '-DfailBuildOnUnusedSuppressionRule=true',
                 '-DsuppressionFile=spring-api/dependency-check-suppressions.xml'):
    require(contract in security_workflow,f'missing Dependency-Check fail-closed contract: {contract}')
suppressions=read('spring-api/dependency-check-suppressions.xml')
suppression_policy=read('spring-api/dependency-suppression-policy.json')
require('CVE-2026-66299' in suppressions and
        suppressions.count('<suppress ') == 1 and
        'until="2026-09-08Z"' in suppressions,
        'Tomcat CVE-2026-66299 suppression must stay exact and time-bounded')
require('CVE-2026-66299' in suppression_policy and
        'allow-unfixed-only' in suppression_policy and
        'current_version' in suppression_policy and
        'package_urls' in suppression_policy and
        'availability' in suppression_policy,
        'temporary dependency suppression must have an NVD-backed availability policy')
for forbidden in ('<cvssBelow>', '<cvssScore>', '<vulnerabilityName regex="true">.*</vulnerabilityName>'):
    require(forbidden not in suppressions,f'broad Dependency-Check suppression forbidden: {forbidden}')
print('[security] OK: Spring security, secret handling, containers and artifact boundaries')
