# Production checklist

## Implemented through release 0.12

- [x] Royal Blackwater Fleet branding across frontend, backend, seeds and infrastructure.
- [x] Responsive RBF brand lockup and two UI/UX refinement iterations.
- [x] Public/member/staff route boundaries in frontend and backend.
- [x] PostgreSQL production mode with Alembic migrations.
- [x] SQLite development mode with lightweight schema creation.
- [x] Docker Compose deployment with explicit health-controlled startup order.
- [x] NGINX reverse proxy and static frontend delivery.
- [x] Let's Encrypt HTTP-01/webroot certificate issuance and twice-daily renewal checks.
- [x] Self-signed bootstrap/fallback TLS for LAN and incomplete DNS setups.
- [x] Uptime Kuma through a dedicated TLS gateway.
- [x] UFW, systemd startup, local backups and smoke tests.
- [x] CI validation for backend tests, migrations, frontend locales/build and shell/Compose syntax.

## Required for the public launch

- [ ] Point `royal-blackwater-fleet.eu` DNS A/AAAA records to the actual public endpoint.
- [ ] Forward TCP 80 and 443 to the Pi; avoid publishing monitoring port 8443 to the internet unless required.
- [ ] Run setup with `--tls-mode letsencrypt` and a monitored contact email.
- [ ] Verify `rbf-hub-cert-renew.timer` and perform a dry renewal test.
- [ ] Replace generated administrator credentials and delete `first-run-credentials.txt`.
- [ ] Configure encrypted off-host backups and test restoration.
- [ ] Add rate limiting for login, registration and upload endpoints.
- [ ] Review SSH policy, disable password login where appropriate and restrict administrative access.
- [ ] Add dependency/container vulnerability scanning to CI.
- [ ] Define an uptime and incident notification channel in Uptime Kuma.

## Recommended hardening

- [ ] Put the Pi behind a VPN or managed reverse proxy if direct exposure is not required.
- [ ] Add central log shipping and disk/storage alerts.
- [ ] Add pagination and retention rules for large activity/log tables.
- [ ] Add an orphaned-upload cleanup job.
- [ ] Consider object storage when uploads outgrow a single-node deployment.
