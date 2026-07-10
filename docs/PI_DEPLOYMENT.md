# Raspberry Pi deployment notes

This is a pragmatic first-deployment setup for a Pi server. It keeps the backend as a normal Python/FastAPI app and serves the compiled frontend statically behind a reverse proxy.

## 1. Prepare folders

```bash
sudo mkdir -p /opt/blackwater-mercenaries-hub/{app,data,uploads,frontend}
sudo chown -R $USER:$USER /opt/blackwater-mercenaries-hub
```

Copy the repository into `/opt/blackwater-mercenaries-hub/app`.

## 2. Backend env

```bash
cd /opt/blackwater-mercenaries-hub/app/backend
cp .env.production.example .env
nano .env
```

Set at least:

```env
APP_ENV=production
DATABASE_URL=sqlite:////opt/blackwater-mercenaries-hub/data/blackwater-hub.db
UPLOAD_DIR=/opt/blackwater-mercenaries-hub/uploads
CORS_ORIGINS=https://your-domain.example
SESSION_COOKIE_SECURE=true
AUTO_SEED=true
SEED_ADMIN_PASSWORD=<long-random-password>
```

For first local LAN testing without HTTPS, use `APP_ENV=development` and `SESSION_COOKIE_SECURE=false`. Switch to production/secure cookies once the reverse proxy serves HTTPS.

## 3. Install backend

```bash
cd /opt/blackwater-mercenaries-hub/app/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e .
blackwater-seed --reset
```

## 4. Build frontend

```bash
cd /opt/blackwater-mercenaries-hub/app/frontend
cp .env.production.example .env
npm ci
npm run build
rsync -a --delete dist/ /opt/blackwater-mercenaries-hub/frontend/
```

For a same-domain reverse proxy, keep `VITE_API_BASE_URL=/api`.

## 5. systemd service

Copy `deployment/pi/blackwater-hub-api.service` to `/etc/systemd/system/` and adjust paths/user if needed:

```bash
sudo cp deployment/pi/blackwater-hub-api.service /etc/systemd/system/blackwater-hub-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now blackwater-hub-api
sudo systemctl status blackwater-hub-api
```

## 6. Reverse proxy

Use `deployment/pi/nginx.conf.example` as a starting point. It proxies `/api` and `/uploads` to Uvicorn and serves the frontend from `/opt/blackwater-mercenaries-hub/frontend`.

## Notes

- Keep `backend/.env` out of Git.
- Back up `/opt/blackwater-mercenaries-hub/data` and `/opt/blackwater-mercenaries-hub/uploads`.
- SQLite is acceptable for a first Pi prototype. PostgreSQL remains the recommended next production step.
