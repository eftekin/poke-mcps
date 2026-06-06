# poke-mcps

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Poke](https://img.shields.io/badge/Poke-iMessage%20AI-black.svg)](https://poke.com)

A collection of MCP servers built for [Poke](https://poke.com), the iMessage AI assistant.

## Servers

| Directory | Description | Data Source | Status |
|-----------|-------------|-------------|--------|
| [`f1/`](./f1/) | Formula 1 live data — standings, laps, telemetry, race control | [OpenF1](https://openf1.org) (free) | ✅ Live |

## How It Works

Each server is an independent Python service using [FastMCP](https://gofastmcp.com), deployed to [Render.com](https://render.com) on the free tier. Once deployed, the server URL is added to Poke as a custom MCP integration.

## Adding a Server to Poke

**Settings → Integrations → Add Custom MCP Server**

| Field | Value |
|-------|-------|
| URL | `https://<your-render-url>/mcp` |
| Auth | None |

## License

[MIT](LICENSE)
