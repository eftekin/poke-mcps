# 🖥️ Poke Assistant MCP

> Local macOS context for [Poke](https://poke.com) — system telemetry, media, Discord activity, and active dev environment.

This server runs **locally on your Mac** and exposes a permanent public URL via a Cloudflare named tunnel. It cannot be deployed to the cloud — it requires direct access to macOS APIs and local processes.

## Tools

| Tool | Description |
|------|-------------|
| `get_mac_telemetry` | CPU usage, RAM, battery level and charging status |
| `get_media_status` | Currently playing track on Spotify or Apple Music |
| `get_discord_activity` | Active game via Lanyard API, Discord IPC, or process scan |
| `get_dev_context` | Running IDE (Antigravity, VS Code, Xcode) with active workspace/window |

## Requirements

- macOS
- Python 3.11+
- [Cloudflare named tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) configured at `.cloudflared/config.yml`
- Lanyard membership for Discord activity ([discord.gg/lanyard](https://discord.gg/lanyard))

## Setup

```bash
# 1. Create virtual environment and install dependencies
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and set POKE_MCP_API_KEY to a secure random token

# 3. Place your Cloudflare tunnel config at .cloudflared/config.yml

# 4. Start the server and tunnel
chmod +x scripts/*.sh
./scripts/start.sh
```

## launchd (Start at Login)

```bash
# Load (registers and starts the service)
launchctl load ~/Developer/poke-mcps/poke-assistant/com.local.poke.assistant.plist

# Unload
launchctl unload ~/Developer/poke-mcps/poke-assistant/com.local.poke.assistant.plist
```

> If you were previously running the old service (`com.local.poke.mcp`), unload it first:
> `launchctl unload ~/Developer/mcp-servers/poke-assistant/com.local.poke.mcp.plist`

## Connect to Poke

**Poke → Settings → Integrations → Add Custom MCP Server**

- **URL**: `https://mcp.eftekin.com/mcp`
- **Auth**: Bearer token (value of `POKE_MCP_API_KEY` from your `.env`)
