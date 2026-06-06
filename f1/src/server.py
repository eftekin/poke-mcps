import httpx
from fastmcp import FastMCP

mcp = FastMCP("F1 Live Data")
BASE = "https://api.openf1.org/v1"


async def _get(path: str, **params) -> list | dict:
    filtered = {k: v for k, v in params.items() if v is not None}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{BASE}/{path}", params=filtered)
        r.raise_for_status()
        return r.json()


async def _resolve_session_key(session_key: int | None) -> int:
    if session_key is not None:
        return session_key
    latest = await _get("sessions", session_key="latest")
    result = latest[0] if isinstance(latest, list) else latest
    return result["session_key"]


@mcp.tool()
async def get_race_schedule(year: int = 2026) -> list:
    """Get the full F1 race calendar for a given year."""
    sessions = await _get("sessions", year=year, session_type="Race")
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
        "sessions",
        year=year,
        session_type=session_type,
        country_name=country_name,
        circuit_short_name=circuit_short_name,
    )


@mcp.tool()
async def get_latest_session() -> dict:
    """Return the currently active or most recently completed session."""
    sessions = await _get("sessions", session_key="latest")
    return sessions[0] if isinstance(sessions, list) and sessions else sessions


@mcp.tool()
async def get_drivers(session_key: int = None) -> list:
    """List all drivers and their metadata for a session. Defaults to the latest session."""
    key = await _resolve_session_key(session_key)
    return await _get("drivers", session_key=key)


@mcp.tool()
async def get_positions(session_key: int = None, driver_number: int = None) -> list:
    """
    Live race standings updated every 4 seconds.
    Omit driver_number to get all drivers, or specify one for a targeted query.
    """
    key = await _resolve_session_key(session_key)
    return await _get("position", session_key=key, driver_number=driver_number)


@mcp.tool()
async def get_intervals(session_key: int = None, driver_number: int = None) -> list:
    """
    Gap to leader and gap to car ahead, updated every 4 seconds during live sessions.
    """
    key = await _resolve_session_key(session_key)
    return await _get("intervals", session_key=key, driver_number=driver_number)


@mcp.tool()
async def get_laps(
    session_key: int = None,
    driver_number: int = None,
    lap_number: int = None,
) -> list:
    """Lap times with sector splits, speed trap, and tyre compound."""
    key = await _resolve_session_key(session_key)
    return await _get("laps", session_key=key, driver_number=driver_number, lap_number=lap_number)


@mcp.tool()
async def get_stints(session_key: int = None, driver_number: int = None) -> list:
    """Tyre stint data: compound, start/end lap, new or used tyre."""
    key = await _resolve_session_key(session_key)
    return await _get("stints", session_key=key, driver_number=driver_number)


@mcp.tool()
async def get_pit_stops(session_key: int = None, driver_number: int = None) -> list:
    """Pit stop records including duration and lap number."""
    key = await _resolve_session_key(session_key)
    return await _get("pit", session_key=key, driver_number=driver_number)


@mcp.tool()
async def get_weather(session_key: int = None) -> list:
    """Track and air conditions: temperature, humidity, wind speed/direction, rainfall."""
    key = await _resolve_session_key(session_key)
    return await _get("weather", session_key=key)


@mcp.tool()
async def get_race_control(session_key: int = None) -> list:
    """Race control messages: safety car, VSC, flags, DRS, penalties."""
    key = await _resolve_session_key(session_key)
    return await _get("race_control", session_key=key)


@mcp.tool()
async def get_team_radio(session_key: int = None, driver_number: int = None) -> list:
    """Team radio recordings with audio URL and transcript where available."""
    key = await _resolve_session_key(session_key)
    return await _get("team_radio", session_key=key, driver_number=driver_number)


@mcp.tool()
async def get_telemetry(session_key: int, driver_number: int, lap_number: int = None) -> list:
    """
    Car telemetry sampled at 3.7 Hz: speed, throttle, brake, RPM, gear, DRS.
    Always specify lap_number — omitting it returns the full session dataset.
    """
    return await _get(
        "car_data",
        session_key=session_key,
        driver_number=driver_number,
        lap_number=lap_number,
    )
