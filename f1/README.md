# F1 Live Data MCP

Real-time Formula 1 data for Poke, powered by the [OpenF1 API](https://openf1.org).

During race weekends, live data is available from 30 minutes before a session starts with ~3 second latency. All historical data from 2023 onwards is included.

## Tools

**Schedule & Sessions**
| Tool | Description |
|------|-------------|
| `get_race_schedule` | Full season calendar |
| `get_sessions` | Filter sessions by year, type, or country |
| `get_latest_session` | Currently active or most recent session |
| `get_meetings` | Grand Prix weekend details and dates |

**Drivers**
| Tool | Description |
|------|-------------|
| `get_drivers` | Driver list, number, team, headshot URL |

**Live Race Data** *(4s refresh during sessions)*
| Tool | Description |
|------|-------------|
| `get_positions` | Live race standings |
| `get_intervals` | Gap to leader and gap ahead |
| `get_race_control` | Safety car, VSC, flags, DRS, penalties |

**Laps & Strategy**
| Tool | Description |
|------|-------------|
| `get_laps` | Lap times with sector splits and tyre compound |
| `get_stints` | Tyre strategy per driver |
| `get_pit_stops` | Pit stop records and durations |

**Car Data** *(3.7 Hz — always specify `lap_number`)*
| Tool | Description |
|------|-------------|
| `get_telemetry` | Speed, throttle, brake, RPM, gear, DRS |
| `get_location` | GPS x/y/z coordinates on track map |

**Conditions & Radio**
| Tool | Description |
|------|-------------|
| `get_weather` | Track/air temperature, humidity, wind, rainfall |
| `get_team_radio` | Radio messages with audio URLs |

**Championship Standings**
| Tool | Description |
|------|-------------|
| `get_driver_standings` | Points, wins, and team per driver |
| `get_constructor_standings` | Points and wins per team |
| `get_race_results` | Official race results with grid and fastest lap |

## Stack

- **Runtime**: Python 3.12
- **Framework**: [FastMCP](https://gofastmcp.com)
- **Transport**: Streamable HTTP
- **Data**: [OpenF1 API](https://openf1.org) (free, no auth)

## Deployment

### Render.com (free tier)

1. Fork this repository
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your fork, set **Root Directory** to `f1`
4. Configure the service:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `fastmcp run src/server.py:mcp --transport streamable-http --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
5. Click **Deploy** — your MCP URL will be `https://<service-name>.onrender.com/mcp`
