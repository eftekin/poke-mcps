#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pkill -f "mcp_server.py" 2>/dev/null && echo "[poke-assistant] Server stopped" || echo "[poke-assistant] Server was not running"
pkill -f "cloudflared tunnel run" 2>/dev/null && echo "[poke-assistant] Tunnel stopped" || echo "[poke-assistant] Tunnel was not running"

rm -f "$DIR/.tunnel-url" "$DIR/.server.pid" "$DIR/.tunnel.pid"
echo "[poke-assistant] Done."
