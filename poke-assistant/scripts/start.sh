#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$DIR/.venv/bin/python3"
CLOUDFLARED="/opt/homebrew/bin/cloudflared"
CF_CONFIG="$DIR/.cloudflared/config.yml"
PORT=8765
LOG_DIR="$DIR/logs"
TUNNEL_URL="https://mcp.eftekin.com/mcp"

mkdir -p "$LOG_DIR"

pkill -f "mcp_server.py" 2>/dev/null || true
pkill -f "cloudflared tunnel run" 2>/dev/null || true
sleep 1

> "$LOG_DIR/server.log"
> "$LOG_DIR/tunnel.log"

PYTHONUNBUFFERED=1 OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES \
  "$PYTHON" "$DIR/mcp_server.py" --transport streamable-http --port "$PORT" \
  >> "$LOG_DIR/server.log" 2>&1 &
SERVER_PID=$!
echo "[poke-assistant] Server started (PID $SERVER_PID, port $PORT)"

sleep 2

"$CLOUDFLARED" tunnel --config "$CF_CONFIG" run \
  >> "$LOG_DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!
echo "[poke-assistant] Tunnel started (PID $TUNNEL_PID)"

echo "$SERVER_PID" > "$DIR/.server.pid"
echo "$TUNNEL_PID" > "$DIR/.tunnel.pid"
echo "$TUNNEL_URL"  > "$DIR/.tunnel-url"

sleep 5

echo ""
echo "┌──────────────────────────────────────────────┐"
echo "│  Poke MCP URL (permanent):                   │"
printf "│  %-44s │\n" "$TUNNEL_URL"
echo "└──────────────────────────────────────────────┘"
echo ""

osascript -e "display notification \"$TUNNEL_URL\" with title \"Poke Assistant Ready\""
