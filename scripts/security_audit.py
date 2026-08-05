#!/usr/bin/env python3
"""Static, fail-closed security invariants for application and deployment boundaries."""
from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

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
password=read('spring-api/src/main/java/eu/royalblackwater/api/security/PasswordHasher.java')
require('ITERATIONS = 600_000' in password and 'PBKDF2WithHmacSHA256' in password,'password hashing policy regressed')
session=read('spring-api/src/main/java/eu/royalblackwater/api/security/SessionTokenService.java')
require('new byte[32]' in session and 'SHA-256' in session,'session token entropy/hash policy regressed')
auth=read('spring-api/src/main/java/eu/royalblackwater/api/account/AuthOperationHandler.java')
for contract in ('.httpOnly(true)','.secure(session.secure())','.sameSite(session.sameSite())','.maxAge(session.ttl())'):
    require(contract in auth,f'session cookie contract missing: {contract}')
secret=read('spring-api/src/main/java/eu/royalblackwater/api/security/FernetSecretBox.java')
require('At least one application encryption key is required' in secret,'secret key must be mandatory')
for forbidden in ('derivedKey(', 'databaseUrl', 'AES/ECB', 'Cipher.getInstance("AES")'):
    require(forbidden not in secret,f'insecure secret-box fallback remains: {forbidden}')

java_root=ROOT/'spring-api/src/main/java'
all_java='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in java_root.rglob('*.java'))
for forbidden in ('Runtime.getRuntime().exec','ProcessBuilder(', 'TrustAll', 'HostnameVerifier', 'setFollowRedirects(true)', 'FetchType.EAGER'):
    require(forbidden not in all_java,f'forbidden Java security pattern: {forbidden}')
require('SKIP LOCKED' in all_java.upper(),'persistent delivery workers must claim rows without duplicate work')

compose=read('infrastructure/compose.yml')
for service in ('api','gateway'):
    match=re.search(rf'(?ms)^  {re.escape(service)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)', compose)
    require(match is not None,f'missing compose service {service}')
    section=match.group(1)
    require('read_only: true' in section,f'{service} filesystem is not read-only')
    require('no-new-privileges:true' in section,f'{service} lacks no-new-privileges')
    require('cap_drop: [ALL]' in section or '- ALL' in section,f'{service} does not drop capabilities')
require('127.0.0.1:${POSTGRES_LOCAL_PORT' in compose,'PostgreSQL may not bind publicly')
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
pom=read('spring-api/pom.xml')
require('<postgresql.version>42.7.12</postgresql.version>' in pom,
        'PostgreSQL JDBC must retain the reviewed security update')
for dockerfile in ('spring-api/Dockerfile','infrastructure/docker/api-runtime.Dockerfile',
                   'infrastructure/docker/frontend.Dockerfile','infrastructure/docker/gateway-runtime.Dockerfile'):
    require('apk upgrade --no-cache' in read(dockerfile),
            f'{dockerfile} must apply Alpine security updates during the image build')
security_workflow=read('.github/workflows/security.yml')
require('org.owasp:dependency-check-maven:12.2.2:check' in security_workflow,
        'OWASP dependency-check must use the reviewed pinned version')
require('NVD_API_KEY: ${{ secrets.NVD_API_KEY }}' in security_workflow and
        'if [[ -n "$NVD_API_KEY" ]]' in security_workflow,
        'OWASP dependency-check must consume only a non-empty GitHub NVD secret')
require('nvdApiKeyEnvironmentVariable=NVD_API_KEY' in security_workflow,
        'OWASP dependency-check must receive its optional NVD key through an environment variable')
print('[security] OK: Spring security, secret handling, containers and artifact boundaries')
