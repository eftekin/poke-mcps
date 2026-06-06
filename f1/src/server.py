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


@mcp.tool()
async def get_sessions(
    year: int = None,
    session_type: str = None,
    country_name: str = None,
    circuit_short_name: str = None,
) -> list:
    """
    Get F1 race sessions (Race, Qualifying, Practice, Sprint).
    Leave all params empty to get the latest/current session.
    session_type options: 'Race', 'Qualifying', 'Practice 1', 'Practice 2', 'Practice 3', 'Sprint'
    """
    return await _get("sessions", year=year, session_type=session_type,
                      country_name=country_name, circuit_short_name=circuit_short_name)


@mcp.tool()
async def get_latest_session() -> dict:
    """Get the most recent or currently active F1 session."""
    sessions = await _get("sessions", session_key="latest")
    return sessions[0] if isinstance(sessions, list) and sessions else sessions


@mcp.tool()
async def get_drivers(session_key: int = None) -> list:
    """
    Get all drivers for a session.
    Use session_key='latest' approach by passing None for the current session.
    """
    if session_key is None:
        latest = await _get("sessions", session_key="latest")
        session_key = latest[0]["session_key"] if isinstance(latest, list) else latest["session_key"]
    return await _get("drivers", session_key=session_key)


@mcp.tool()
async def get_positions(session_key: int = None, driver_number: int = None) -> list:
    """
    Get real-time race positions (updates every 4 seconds during live sessions).
    Returns the latest position data for all drivers or a specific driver.
    """
    if session_key is None:
        latest = await _get("sessions", session_key="latest")
        session_key = latest[0]["session_key"] if isinstance(latest, list) else latest["session_key"]
    return await _get("position", session_key=session_key, driver_number=driver_number)


@mcp.tool()
async def get_laps(session_key: int = None, driver_number: int = None, lap_number: int = None) -> list:
    """
    Get lap times with sector times, speed traps, and compound info.
    Specify driver_number for a single driver or lap_number for a specific lap.
    """
    if session_key is None:
        latest = await _get("sessions", session_key="latest")
        session_key = latest[0]["session_key"] if isinstance(latest, list) else latest["session_key"]
    return await _get("laps", session_key=session_key, driver_number=driver_number, lap_number=lap_number)


@mcp.tool()
async def get_pit_stops(session_key: int = None, driver_number: int = None) -> list:
    """Get pit stop data including duration and lap number."""
    if session_key is None:
        latest = await _get("sessions", session_key="latest")
        session_key = latest[0]["session_key"] if isinstance(latest, list) else latest["session_key"]
    return await _get("pit", session_key=session_key, driver_number=driver_number)


@mcp.tool()
async def get_weather(session_key: int = None) -> list:
    """
    Get weather data: track/air temperature, humidity, wind speed/direction, rainfall.
    Returns readings throughout the session.
    """
    if session_key is None:
        latest = await _get("sessions", session_key="latest")
        session_key = latest[0]["session_key"] if isinstance(latest, list) else latest["session_key"]
    return await _get("weather", session_key=session_key)


@mcp.tool()
async def get_race_control(session_key: int = None) -> list:
    """
    Get race control messages: safety car, VSC, flags, penalties, DRS status.
    Essential for following live races.
    """
    if session_key is None:
        latest = await _get("sessions", session_key="latest")
        session_key = latest[0]["session_key"] if isinstance(latest, list) else latest["session_key"]
    return await _get("race_control", session_key=session_key)


@mcp.tool()
async def get_team_radio(session_key: int = None, driver_number: int = None) -> list:
    """Get team radio recordings (URL to audio clip + transcript if available)."""
    if session_key is None:
        latest = await _get("sessions", session_key="latest")
        session_key = latest[0]["session_key"] if isinstance(latest, list) else latest["session_key"]
    return await _get("team_radio", session_key=session_key, driver_number=driver_number)


@mcp.tool()
async def get_intervals(session_key: int = None, driver_number: int = None) -> list:
    """
    Get live gap-to-leader and gap-to-car-ahead intervals.
    Updates every 4 seconds during live sessions.
    """
    if session_key is None:
        latest = await _get("sessions", session_key="latest")
        session_key = latest[0]["session_key"] if isinstance(latest, list) else latest["session_key"]
    return await _get("intervals", session_key=session_key, driver_number=driver_number)


@mcp.tool()
async def get_stints(session_key: int = None, driver_number: int = None) -> list:
    """Get tyre stint data: compound, lap start/end, new/used tyre."""
    if session_key is None:
        latest = await _get("sessions", session_key="latest")
        session_key = latest[0]["session_key"] if isinstance(latest, list) else latest["session_key"]
    return await _get("stints", session_key=session_key, driver_number=driver_number)


@mcp.tool()
async def get_telemetry(session_key: int, driver_number: int, lap_number: int = None) -> list:
    """
    Get car telemetry: speed, throttle, brake, RPM, gear, DRS at 3.7 Hz.
    Warning: returns large datasets. Specify lap_number to limit results.
    """
    return await _get("car_data", session_key=session_key, driver_number=driver_number)


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
