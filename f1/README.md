# F1 Live Data MCP

Real-time Formula 1 data server powered by the [OpenF1 API](https://openf1.org) — free, no sign-up required.

## Tools

| Tool | Description |
|------|-------------|
| `get_race_schedule` | Full season calendar |
| `get_latest_session` | Current or most recent session |
| `get_sessions` | Filter sessions by year, type, or country |
| `get_drivers` | Driver list for a session |
| `get_positions` | Live standings (updates every 4s) |
| `get_intervals` | Gap to leader and gap ahead |
| `get_laps` | Lap times and sector splits |
| `get_stints` | Tyre strategy data |
| `get_pit_stops` | Pit stop records |
| `get_weather` | Track and air conditions |
| `get_race_control` | Safety car, flags, penalties |
| `get_team_radio` | Radio messages |
| `get_telemetry` | Car telemetry (speed, throttle, brake, gear) |

## Deploy to Render.com (Free)

1. Go to [render.com](https://render.com) → New → Web Service
2. Connect this repository, set **Root Directory** to `f1`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `fastmcp run src/server.py:mcp --transport streamable-http --host 0.0.0.0 --port $PORT`
5. **Instance Type**: Free → Deploy

## Adding to Poke

Settings → Integrations → Add Custom MCP Server

- **URL**: `https://<your-render-url>/mcp`
- **Auth**: None
