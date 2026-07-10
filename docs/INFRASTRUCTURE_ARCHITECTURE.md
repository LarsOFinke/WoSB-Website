# Infrastructure architecture

```text
Browser / LAN / Internet
          |
       80 / 443
          |
    NGINX gateway  <---- HTTP-01 webroot ---- Certbot
      |         \
      |          static Vue application
      |
  /api, /uploads
      |
   FastAPI API
      |
 internal backend network
      |
 PostgreSQL 16
```

Optional monitoring uses a second NGINX TLS endpoint on port 8443. Uptime Kuma itself remains on
the private backend network.

One-shot lifecycle services run before the API:

```text
PostgreSQL healthy -> Alembic migration -> idempotent seed -> API ready -> edge gateways
```

A failed migration prevents the API and gateway from being reported as healthy.

## Persistent paths

```text
infrastructure/data/postgres/    PostgreSQL cluster
infrastructure/data/uploads/     user uploads
infrastructure/data/certs/       active gateway certificate/key
infrastructure/data/acme/        HTTP-01 challenge webroot
infrastructure/data/letsencrypt/ Certbot account, renewal and lineage state
infrastructure/data/nginx/       NGINX logs
infrastructure/data/uptime-kuma/ optional monitoring state
infrastructure/data/backups/     local database/file backups
```

## TLS lifecycle

1. Setup creates a self-signed bootstrap certificate so NGINX can start immediately.
2. NGINX exposes `/.well-known/acme-challenge/` over HTTP.
3. Certbot requests the certificate for `royal-blackwater-vanguards.eu` through the webroot.
4. The managed lineage is copied to the stable gateway certificate paths.
5. NGINX and the monitoring gateway reload without resetting application data.
6. `rbv-hub-cert-renew.timer` checks twice daily and repeats the sync after renewal.

`TLS_MODE=auto` preserves the bootstrap certificate when public validation is not yet possible;
`TLS_MODE=letsencrypt` fails fast if a trusted certificate cannot be issued.

## Security baseline

- PostgreSQL and FastAPI are not directly exposed to the LAN.
- PostgreSQL's diagnostic port is loopback-only.
- Production cookies are secure.
- Secrets and first-run credentials are Git-ignored and mode `0600`.
- Containers use `no-new-privileges`; the API root filesystem is read-only.
- UFW permits only the configured SSH, application and optional monitoring ports.
- Monitoring can remain LAN/VPN-only while the main site is public.

Before public use, configure off-host encrypted backups, review SSH access, add rate limiting and run
continuous dependency/container vulnerability scans.
