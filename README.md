# poke-mcps

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Built for Poke](https://img.shields.io/badge/Built%20for-Poke-black.svg)](https://poke.com)

Custom MCP servers that extend [Poke](https://poke.com) — the iMessage AI assistant — with real-world data sources.

## Servers

| | Server | Description | Deploy | URL |
|---|--------|-------------|--------|-----|
| 🏎️ | [`f1-workers/`](./f1-workers/) | Formula 1 live data — standings, laps, telemetry, race control | ☁️ Cloudflare Workers | `f1-mcp.eftekin.com/mcp` |
| 🖥️ | [`poke-assistant/`](./poke-assistant/) | macOS context — system telemetry, media, Discord activity, active IDE | 🏠 Local + Cloudflare Tunnel | `mcp.eftekin.com/mcp` |

## How It Works

```
Poke (iMessage) → MCP Server → Data Source (API)
```

- **f1-workers**: TypeScript on [Cloudflare Workers](https://workers.cloudflare.com) — no cold starts, always on, free tier
- **poke-assistant**: Python on your Mac, exposed via a [Cloudflare named tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)

## Adding a Server to Poke

**Poke → Settings → Integrations → Add Custom MCP Server**

| Server | URL | Auth |
|--------|-----|------|
| F1 Live Data | `https://f1-mcp.eftekin.com/mcp` | None |
| Poke Assistant | `https://mcp.eftekin.com/mcp` | Bearer token |

See each server's README for setup and deployment details.

## License

[MIT](LICENSE)
