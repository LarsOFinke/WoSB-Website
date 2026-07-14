# Standalone Discord bot management

The website and Discord bot remain separate repositories. The website Staff Panel only writes a narrowly scoped request file. A root-owned systemd host runner performs one of five allow-listed operations: install, update, start, stop or restart.

## Host configuration

After a normal website update, edit:

```text
/etc/rbf-hub/discord-bot-manager.env
```

Set the private Git URL, branch and installation directory. Repository URLs are host configuration and are not accepted from browser requests.

## Staff Panel workflow

1. Publish the standalone bot repository to a private Git remote.
2. Configure `/etc/rbf-hub/discord-bot-manager.env`.
3. Open **Staff Panel → Status → Discord bot**.
4. Select **Install bot**.
5. Configure bot secrets and channel routing in:
   - `/etc/rbf-discord-bot/bot.env`
   - `/etc/rbf-discord-bot/bot.yaml`
6. Restart the bot through the Staff Panel.
7. Create a website outbound webhook with endpoint:

```text
https://royal-blackwater-fleet.eu/integrations/discord/webhooks/rbf
```

8. Copy the website-generated signing secret into `RBF_WEBHOOK_SECRET` in the bot environment.

The public reverse proxy exposes only the signed webhook receiver. The bot management endpoint is not proxied.
