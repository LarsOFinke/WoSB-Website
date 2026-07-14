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
```

These are not bot runtime variables. They tell the root-owned website host runner where it may clone and update the standalone repository. Browser requests cannot change the repository URL, branch or install path.

The runner reads this file on every operation. Editing it does not require restarting the website. A systemd daemon reload is needed only when unit definitions themselves change; the normal website installation/update workflow handles that.

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
