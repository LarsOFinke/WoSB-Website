from pathlib import Path

from app.modules.admin.schemas.discord_bot import DiscordBotConfigurationStatus


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")


def test_host_runner_writes_a_docker_reachable_bot_binding() -> None:
    context = _read("infrastructure/scripts/discord-bot/context.sh")
    configurator = _read("infrastructure/scripts/discord-bot/apply-configuration.py")
    example = _read("infrastructure/config/discord-bot-manager.env.example")

    assert 'RBF_DISCORD_BOT_BIND_HOST:-0.0.0.0' in context
    assert 'raw_config["server"]["host"] = os.environ["RBF_DISCORD_BOT_BIND_HOST"]' in configurator
    assert "RBF_DISCORD_BOT_BIND_HOST=0.0.0.0" in example
    assert "RBF_DISCORD_BOT_FIREWALL_MODE=auto" in example
    assert "RBF_DISCORD_BOT_PORT" not in example


def test_gateway_access_script_scopes_firewall_and_checks_health() -> None:
    helper = _read("infrastructure/scripts/services/configure-discord-bot-gateway.sh")

    assert "host.docker.internal" in helper
    assert 'ufw allow from "$subnet" to "$HOST_GATEWAY_IP" port "$BOT_PORT"' in helper
    assert "http://host.docker.internal:${BOT_PORT}/health" in helper
    assert "ufw allow 8765/tcp" not in helper
    assert "Loopback-Adresse" in helper


def test_gateway_route_targets_the_host_managed_bot() -> None:
    compose = _read("infrastructure/compose.yml")
    nginx = _read("infrastructure/nginx/default.conf")

    assert '"host.docker.internal:host-gateway"' in compose
    assert "proxy_pass http://host.docker.internal:8765/webhooks/rbf;" in nginx


def test_configuration_status_exposes_non_secret_network_metadata() -> None:
    status = DiscordBotConfigurationStatus.model_validate(
        {
            "bind_host": "0.0.0.0",
            "listen_port": 8765,
            "firewall_mode": "auto",
            "public_webhook_path": "/webhooks/rbf",
        }
    )

    assert status.bind_host == "0.0.0.0"
    assert status.listen_port == 8765
    assert status.firewall_mode == "auto"
