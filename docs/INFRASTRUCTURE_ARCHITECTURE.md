# Infrastructure architecture

```text
Browser / LAN / Internet
          |
       80 / 443
          |
    NGINX gateway
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

One-shot lifecycle services run before the API:

```text
migrate -> Alembic upgrade head
seed    -> catalog, fleet and initial administrator data
```

The compose stack intentionally separates these concerns from the long-running API. A failed
migration prevents the API and gateway from reporting a healthy deployment.

## Persistent paths

```text
infrastructure/data/postgres/    PostgreSQL cluster
infrastructure/data/uploads/     user uploads
infrastructure/data/certs/       TLS certificate and key
infrastructure/data/nginx/       NGINX logs
infrastructure/data/uptime-kuma/ optional monitoring state
infrastructure/data/backups/     local database/file backups
```

## Security baseline

- PostgreSQL and FastAPI are not directly exposed to the LAN.
- PostgreSQL's diagnostic port is loopback-only.
- application cookies are secure in production;
- TLS is available on the first boot through a generated self-signed certificate;
- secrets and first-run credentials are Git-ignored and mode `0600`;
- containers use `no-new-privileges`;
- the API root filesystem is read-only except for `/tmp` and the upload volume;
- UFW permits SSH, HTTP and HTTPS only.

The alpha setup is a strong baseline, not a substitute for public-internet hardening. Before a
public launch, replace the self-signed certificate, configure off-host backups, review SSH
access, add rate limiting and run vulnerability scans in CI.
