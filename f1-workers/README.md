# 🏎️ F1 Live Data MCP

> Formula 1 data for [Poke](https://poke.com) — live timing, telemetry, standings, and more.

Deployed on [Cloudflare Workers](https://workers.cloudflare.com) at `f1-mcp.eftekin.com/mcp`. No cold starts. No keep-alive needed.

Powered by [OpenF1](https://openf1.org) (live session data) and [Jolpica F1](https://jolpi.ca) (official results and standings). No API keys required.

During race weekends, live data streams from 30 minutes before session start with ~3s latency.

## Tools

**Schedule & Sessions**
| Tool | Description |
|------|-------------|
| `get_race_schedule` | Full season calendar with circuits and dates |
| `get_sessions` | Filter sessions by year, type, or country |
| `get_latest_session` | Currently active or most recent session |
| `get_meetings` | Grand Prix weekend info and session list |

**Drivers**
| Tool | Description |
|------|-------------|
| `get_drivers` | Driver numbers, abbreviations, team, headshot URL |

**Live Timing** *(updates every 4s during sessions)*
| Tool | Description |
|------|-------------|
| `get_positions` | Current race order |
| `get_intervals` | Gap to leader and gap ahead |
| `get_race_control` | Safety car, VSC, flags, DRS, penalties |

**Laps & Strategy**
| Tool | Description |
|------|-------------|
| `get_laps` | Lap times, sector splits, tyre compound |
| `get_stints` | Tyre strategy and stint history |
| `get_pit_stops` | Pit stop lap, duration, and time |

**Car Data** *(3.7 Hz — specify `lap_number` to avoid large payloads)*
| Tool | Description |
|------|-------------|
| `get_telemetry` | Speed, throttle, brake, RPM, gear, DRS |
| `get_location` | GPS coordinates (x/y/z) on track map |

**Conditions & Radio**
| Tool | Description |
|------|-------------|
| `get_weather` | Track/air temp, humidity, wind, rainfall |
| `get_team_radio` | Radio clips with audio URL |

**Championship**
| Tool | Description |
|------|-------------|
| `get_driver_standings` | Points, wins, and team per driver |
| `get_constructor_standings` | Points and wins per constructor |
| `get_race_results` | Full results with grid, status, fastest lap |

## Stack

| | |
|--|--|
| Runtime | [Cloudflare Workers](https://workers.cloudflare.com) |
| Language | TypeScript |
| Live data | [OpenF1 API](https://openf1.org) — free, no auth |
| Results & standings | [Jolpica F1](https://jolpi.ca) — free, no auth |

## Deploy

```bash
npm install
npx wrangler deploy
```

Requires a [Cloudflare account](https://cloudflare.com) and `wrangler login`.

## Connect to Poke

**Poke → Settings → Integrations → Add Custom MCP Server**

- **URL**: `https://f1-mcp.eftekin.com/mcp`
- **Auth**: None
