# poke-mcps

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Built for Poke](https://img.shields.io/badge/Built%20for-Poke-black.svg)](https://poke.com)

Custom MCP servers that extend [Poke](https://poke.com) — the iMessage AI assistant — with real-world data sources.

## Servers

| | Server | Description | Deploy |
|---|--------|-------------|--------|
| 🏎️ | [`f1/`](./f1/) | Formula 1 live data — standings, laps, telemetry, race control, championship | ☁️ Cloud (Render) |
| 🖥️ | [`poke-assistant/`](./poke-assistant/) | macOS context — system telemetry, media, Discord activity, active IDE | 🏠 Local + Cloudflare Tunnel |

## How It Works

Each server is an independent Python service using [FastMCP](https://gofastmcp.com) deployed to [Render.com](https://render.com) free tier. Poke discovers available tools automatically — no configuration needed beyond adding the URL.

```
Poke (iMessage) → MCP Server (Render) → Data Source (API)
```

## Adding a Server to Poke

**Poke → Settings → Integrations → Add Custom MCP Server**

- **URL**: `https://<your-render-url>/mcp`
- **Auth**: None

See each server's README for the specific deploy URL and setup steps.

## License

[MIT](LICENSE)
