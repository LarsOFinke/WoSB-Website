# Standalone Discord bot management

The website and Discord bot remain separate repositories. The website Staff Panel talks only to a narrowly scoped request-file interface. A root-owned systemd host runner performs allow-listed installation, service and configuration operations.

## Two separate configuration levels

### Website host-runner source configuration

```text
/etc/rbf-hub/discord-bot-manager.env
```

This file contains only:

```bash
RBF_DISCORD_BOT_REPO_URL=git@github.com:your-org/royal-blackwater-discord-bot.git
RBF_DISCORD_BOT_BRANCH=main
RBF_DISCORD_BOT_INSTALL_DIR=/opt/rbf-discord-bot
RBF_DISCORD_BOT_GIT_SSH_KEY_FILE=/root/.ssh/rbf_discord_bot
RBF_DISCORD_BOT_GIT_KNOWN_HOSTS_FILE=/root/.ssh/rbf-discord-known_hosts
RBF_DISCORD_BOT_GIT_SSH_PORT=22
```

These are not bot runtime variables. They tell the root-owned website host runner where it may clone and update the standalone repository. Browser requests cannot change the repository URL, branch, SSH identity or install path.

The explicit SSH settings are recommended for private repositories. The manager is a root-owned, non-interactive systemd service and therefore does not inherit the login user's `HOME`, `ssh-agent` or SSH configuration. A clone that works in an interactive user shell can otherwise still fail in the Staff Panel. The configured private key should be an unencrypted, read-only deploy key dedicated to the bot repository.

The manager performs `git clone` directly during installation and lets `git fetch`/`git pull` run during updates. It deliberately does not require a separate `git ls-remote` preflight. With the same URL, identity and user context, clone and ls-remote use the same Git transport; different results normally indicate a different URL or SSH context.

The runner reads this file on every operation. Editing it does not require restarting the website. A systemd daemon reload is needed only when unit definitions themselves change; the normal website installation/update workflow handles that.

For GitHub, prepare the dedicated host-key file and verify the exact key non-interactively:

```bash
sudo install -d -m 700 -o root -g root /root/.ssh

sudo ssh-keygen \
  -t ed25519 \
  -a 100 \
  -f /root/.ssh/rbf_discord_bot \
  -C "rbf-discord-bot@$(hostname)" \
  -N ""

sudo chown root:root \
  /root/.ssh/rbf_discord_bot \
  /root/.ssh/rbf_discord_bot.pub

sudo chmod 600 /root/.ssh/rbf_discord_bot
sudo chmod 644 /root/.ssh/rbf_discord_bot.pub

sudo cat /root/.ssh/rbf_discord_bot.pub
```

```bash
sudo install -d -m 0700 /root/.ssh
sudo ssh-keyscan -H github.com | sudo tee /root/.ssh/rbf-discord-known_hosts >/dev/null
sudo chmod 0600 /root/.ssh/rbf_discord_bot /root/.ssh/rbf-discord-known_hosts

sudo -H env GIT_SSH_COMMAND='/usr/bin/ssh -F /dev/null -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/root/.ssh/rbf-discord-known_hosts -i /root/.ssh/rbf_discord_bot' \
  git clone --depth 1 --branch main --single-branch \
  git@github.com:your-org/royal-blackwater-discord-bot.git /tmp/rbf-discord-bot-clone-test
sudo rm -rf /tmp/rbf-discord-bot-clone-test
```

This clone test mirrors the Staff Panel runner more closely than a test performed as the interactive deployment user.

### Bot runtime configuration

After the bot is installed, the administrator form writes validated values to:

```text
/etc/rbf-discord-bot/bot.env
/etc/rbf-discord-bot/bot.yaml
```

The form manages:

- Discord bot token,
- website signing secret,
- website base URL,
- channel IDs,
- signature tolerance,
- Discord request timeout and retry count,
- notification suppression,
- optional immediate restart.

Stored secrets are never returned to the browser. Blank password fields preserve existing secrets. The request file is created with mode `0600`, consumed by the root-owned runner and removed after processing.

## Recommended workflow

1. Publish the standalone bot repository to a private remote.
2. Configure `/etc/rbf-hub/discord-bot-manager.env` on the website host.
3. Ensure `rbf-hub-discord-bot-manager.path` is enabled.
4. Open **Staff Panel → Status → Discord bot**.
5. Select **Install bot**.
6. Fill the newly available runtime configuration form.
7. In **Staff Panel → Integrations**, create an outbound webhook with endpoint:

```text
https://royal-blackwater-fleet.eu/integrations/discord/webhooks/rbf
```

8. Copy that integration's generated signing secret into the bot configuration form.
9. Save with **Restart after saving** enabled.
10. Send a test delivery.

The public reverse proxy exposes only the signed webhook receiver. The bot management endpoint is not proxied.

## Testing webhook DNS from the website API

The outbound webhook sender runs in the Compose service `api`. Use that service name for diagnostics:

```bash
sudo docker compose -f infrastructure/compose.yml exec -T api \
  python - <<'PY'
import socket
print(socket.getaddrinfo("royal-blackwater-fleet.eu", 443))
PY
```

A Compose error mentioning `service "backend" is not running` means the wrong service name was used; there is no `backend` service in this repository. A DNS resolution error from `api` occurs before HMAC validation and is unrelated to the configured website signing secret.

## Docker gateway network and firewall

The public Nginx gateway runs in Docker and forwards only the signed receiver path to:

```text
http://host.docker.internal:8765/webhooks/rbf
```

The bot therefore must listen on an address reachable from Docker. The host runner writes `0.0.0.0:8765` by default; `127.0.0.1` is intentionally rejected for this integration because it would cause an upstream timeout and HTTP 504.

Add these host-runner values to `/etc/rbf-hub/discord-bot-manager.env`:

```bash
RBF_DISCORD_BOT_BIND_HOST=0.0.0.0
RBF_DISCORD_BOT_FIREWALL_MODE=auto
```

In `auto` mode the root-owned runner:

- discovers the running website gateway container,
- reads its private Docker networks and `host.docker.internal` address,
- adds idempotent UFW rules from those private subnets to the bot port,
- never adds a public `8765/tcp` allow rule,
- checks `/health` from inside the gateway after configure, start, restart and update operations.

If the host firewall is managed outside UFW, set:

```bash
RBF_DISCORD_BOT_FIREWALL_MODE=external
```

The external firewall must then permit only the website gateway Docker subnets to the Docker host gateway on the fixed bot port 8765. Do not expose port 8765 to the public Internet.

A successful network check looks like:

```bash
sudo docker compose -f infrastructure/compose.yml exec -T gateway \
  sh -lc 'wget -S -O- -T 5 http://host.docker.internal:8765/health'
```

The response must be HTTP 200 with a JSON body containing `"status":"ok"`. HTTP 504 on the public webhook route means the gateway could not receive a timely response from this internal endpoint.
