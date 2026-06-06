import httpx
from fastmcp import FastMCP

mcp = FastMCP("F1 Live Data")
OPENF1 = "https://api.openf1.org/v1"
JOLPICA = "https://api.jolpi.ca/ergast/f1"


async def _get(base: str, path: str, **params) -> list | dict:
    filtered = {k: v for k, v in params.items() if v is not None}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{base}/{path}", params=filtered)
        r.raise_for_status()
        return r.json()


async def _resolve_session_key(session_key: int | None) -> int:
    if session_key is not None:
        return session_key
    latest = await _get(OPENF1, "sessions", session_key="latest")
    result = latest[0] if isinstance(latest, list) else latest
    return result["session_key"]


# ── Schedule & Sessions ────────────────────────────────────────────────────────

@mcp.tool()
async def get_race_schedule(year: int = 2026) -> list:
    """Full F1 race calendar for a given year with country, circuit, and date."""
    sessions = await _get(OPENF1, "sessions", year=year, session_type="Race")
    return [
        {
            "round": i + 1,
            "country": s.get("country_name"),
            "circuit": s.get("circuit_short_name"),
            "date_start": s.get("date_start"),
            "session_key": s.get("session_key"),
        }
        for i, s in enumerate(sessions)
    ]


@mcp.tool()
async def get_sessions(
    year: int = None,
    session_type: str = None,
    country_name: str = None,
    circuit_short_name: str = None,
) -> list:
    """
    List F1 sessions filtered by any combination of parameters.
    session_type: 'Race' | 'Qualifying' | 'Sprint' | 'Practice 1' | 'Practice 2' | 'Practice 3'
    """
    return await _get(
        OPENF1, "sessions",
        year=year,
        session_type=session_type,
        country_name=country_name,
        circuit_short_name=circuit_short_name,
    )


@mcp.tool()
async def get_latest_session() -> dict:
    """Currently active or most recently completed session."""
    sessions = await _get(OPENF1, "sessions", session_key="latest")
    return sessions[0] if isinstance(sessions, list) and sessions else sessions


@mcp.tool()
async def get_meetings(year: int = None, country_name: str = None) -> list:
    """
    Grand Prix weekend details: official name, location, circuit, dates.
    A meeting groups all sessions (FP1–3, Qualifying, Race) for one GP weekend.
    """
    return await _get(OPENF1, "meetings", year=year, country_name=country_name)


# ── Drivers ───────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_drivers(session_key: int = None) -> list:
    """All drivers with number, abbreviation, team, and headshot URL. Defaults to latest session."""
    key = await _resolve_session_key(session_key)
    return await _get(OPENF1, "drivers", session_key=key)


# ── Live Race Data ─────────────────────────────────────────────────────────────

@mcp.tool()
async def get_positions(session_key: int = None, driver_number: int = None) -> list:
    """
    Live race standings refreshed every 4 seconds.
    Omit driver_number for all drivers, or specify one for a targeted query.
    """
    key = await _resolve_session_key(session_key)
    return await _get(OPENF1, "position", session_key=key, driver_number=driver_number)


@mcp.tool()
async def get_intervals(session_key: int = None, driver_number: int = None) -> list:
    """Gap to leader and gap to car ahead, refreshed every 4 seconds during live sessions."""
    key = await _resolve_session_key(session_key)
    return await _get(OPENF1, "intervals", session_key=key, driver_number=driver_number)


@mcp.tool()
async def get_race_control(session_key: int = None) -> list:
    """Race control messages: safety car, VSC, flags, DRS zones, penalties."""
    key = await _resolve_session_key(session_key)
    return await _get(OPENF1, "race_control", session_key=key)


# ── Laps & Strategy ───────────────────────────────────────────────────────────

@mcp.tool()
async def get_laps(
    session_key: int = None,
    driver_number: int = None,
    lap_number: int = None,
) -> list:
    """Lap times with sector splits, speed trap, and tyre compound per lap."""
    key = await _resolve_session_key(session_key)
    return await _get(OPENF1, "laps", session_key=key, driver_number=driver_number, lap_number=lap_number)


@mcp.tool()
async def get_stints(session_key: int = None, driver_number: int = None) -> list:
    """Tyre stint data: compound, start/end lap, new or used tyre."""
    key = await _resolve_session_key(session_key)
    return await _get(OPENF1, "stints", session_key=key, driver_number=driver_number)


@mcp.tool()
async def get_pit_stops(session_key: int = None, driver_number: int = None) -> list:
    """Pit stop records: lap number, pit lane duration, and total stop duration."""
    key = await _resolve_session_key(session_key)
    return await _get(OPENF1, "pit", session_key=key, driver_number=driver_number)


# ── Car Data ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_telemetry(session_key: int, driver_number: int, lap_number: int = None) -> list:
    """
    Car telemetry at 3.7 Hz: speed, throttle %, brake, RPM, gear, DRS status.
    Always specify lap_number — omitting it returns the entire session dataset.
    """
    return await _get(
        OPENF1, "car_data",
        session_key=session_key,
        driver_number=driver_number,
        lap_number=lap_number,
    )


@mcp.tool()
async def get_location(session_key: int, driver_number: int, lap_number: int = None) -> list:
    """
    GPS coordinates at 3.7 Hz: x/y position on track map and z (altitude).
    Always specify lap_number to avoid retrieving the full session dataset.
    """
    return await _get(
        OPENF1, "location",
        session_key=session_key,
        driver_number=driver_number,
        lap_number=lap_number,
    )


# ── Weather & Radio ───────────────────────────────────────────────────────────

@mcp.tool()
async def get_weather(session_key: int = None) -> list:
    """Track and air conditions: temperature, humidity, wind speed/direction, rainfall."""
    key = await _resolve_session_key(session_key)
    return await _get(OPENF1, "weather", session_key=key)


@mcp.tool()
async def get_team_radio(session_key: int = None, driver_number: int = None) -> list:
    """Team radio recordings with audio URL and transcript where available."""
    key = await _resolve_session_key(session_key)
    return await _get(OPENF1, "team_radio", session_key=key, driver_number=driver_number)


# ── Championship Standings ─────────────────────────────────────────────────────

@mcp.tool()
async def get_driver_standings(year: int = 2026, round: int = None) -> list:
    """
    Driver championship standings: points, wins, and constructor per driver.
    Omit round to get the latest standings for the season.
    """
    path = f"{year}/{round}/driverStandings.json" if round else f"{year}/driverStandings.json"
    data = await _get(JOLPICA, path)
    standings = data["MRData"]["StandingsTable"]["StandingsLists"]
    if not standings:
        return []
    return [
        {
            "position": int(s["position"]),
            "driver": f"{s['Driver']['givenName']} {s['Driver']['familyName']}",
            "code": s["Driver"].get("code"),
            "team": s["Constructors"][0]["name"] if s["Constructors"] else None,
            "points": float(s["points"]),
            "wins": int(s["wins"]),
        }
        for s in standings[0]["DriverStandings"]
    ]


@mcp.tool()
async def get_constructor_standings(year: int = 2026, round: int = None) -> list:
    """
    Constructor championship standings: points and wins per team.
    Omit round to get the latest standings for the season.
    """
    path = f"{year}/{round}/constructorStandings.json" if round else f"{year}/constructorStandings.json"
    data = await _get(JOLPICA, path)
    standings = data["MRData"]["StandingsTable"]["StandingsLists"]
    if not standings:
        return []
    return [
        {
            "position": int(s["position"]),
            "team": s["Constructor"]["name"],
            "nationality": s["Constructor"].get("nationality"),
            "points": float(s["points"]),
            "wins": int(s["wins"]),
        }
        for s in standings[0]["ConstructorStandings"]
    ]


@mcp.tool()
async def get_race_results(year: int = 2026, round: int = None) -> list:
    """
    Official race results with final positions, points, fastest lap, and grid positions.
    Omit round to get the most recent race result.
    """
    path = f"{year}/{round}/results.json" if round else f"{year}/last/results.json"
    data = await _get(JOLPICA, path)
    races = data["MRData"]["RaceTable"]["Races"]
    if not races:
        return []
    race = races[0]
    return {
        "race": race["raceName"],
        "circuit": race["Circuit"]["circuitName"],
        "date": race["date"],
        "results": [
            {
                "position": int(r["position"]),
                "driver": f"{r['Driver']['givenName']} {r['Driver']['familyName']}",
                "team": r["Constructor"]["name"],
                "grid": int(r["grid"]),
                "laps": int(r["laps"]),
                "status": r["status"],
                "points": float(r["points"]),
                "fastest_lap": r.get("FastestLap", {}).get("Time", {}).get("time"),
            }
            for r in race["Results"]
        ],
    }
