#!/usr/bin/env python3
"""
Poke Kitchen — Local MCP Server for macOS
Tools: get_dev_context, get_media_status, get_mac_telemetry, get_discord_activity
Transport: stdio (default) | streamable-http | sse
"""

import argparse
import json
import os
import socket
import struct
import subprocess
import time
import psutil
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings

# .env loader
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

_API_KEY = os.environ.get("POKE_MCP_API_KEY", "")

_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")
_parser.add_argument("--host", default="127.0.0.1")
_parser.add_argument("--port", type=int, default=8765)
_args, _ = _parser.parse_known_args()

_security = TransportSecuritySettings(
    allowed_hosts=["mcp.eftekin.com", "127.0.0.1", "127.0.0.1:8765", "localhost", "localhost:8765"],
    allowed_origins=["https://mcp.eftekin.com"],
)

mcp = FastMCP("poke-assistant", host=_args.host, port=_args.port, transport_security=_security)

# Prime psutil CPU counter — first real call will be instant (no 250 ms sleep)
psutil.cpu_percent(interval=None)

# Persistent HTTP client — reuses TCP/TLS connection across Lanyard calls
_http = httpx.Client(timeout=5.0)


# ---------------------------------------------------------------------------
# Bearer token auth middleware
# ---------------------------------------------------------------------------

class _BearerAuth:
    def __init__(self, app, token: str):
        if not token:
            raise ValueError("_BearerAuth requires a non-empty token")
        self._app = app
        self._token = token.encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            auth = next(
                (v for k, v in scope.get("headers", []) if k == b"authorization"),
                b"",
            )
            if auth != b"Bearer " + self._token:
                await send({
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"text/plain; charset=utf-8"),
                        (b"www-authenticate", b'Bearer realm="poke-mcp"'),
                    ],
                })
                await send({"type": "http.response.body", "body": b"Unauthorized", "more_body": False})
                return
        await self._app(scope, receive, send)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IDE_PROCESS_NAMES: dict[str, list[str]] = {
    "antigravity": ["Antigravity", "antigravity", "ag-electron", "ag-helper"],
    "vscode":      ["Code", "code", "Code Helper (Plugin)", "Code Helper (Renderer)", "Code Helper"],
    "xcode":       ["Xcode", "xcodebuild", "XCBBuildService"],
}

# (applescript, result_key, fallback_message)
_IDE_APPLESCRIPT: dict[str, tuple[str, str, str]] = {
    "vscode": (
        'tell application "Visual Studio Code"\n'
        '    if (count of windows) > 0 then\n'
        '        return name of front window\n'
        '    else\n        return "No open windows"\n    end if\nend tell',
        "active_window",
        "[VS Code window title unavailable — grant Accessibility permission]",
    ),
    "xcode": (
        'tell application "Xcode"\n'
        '    if (count of workspace documents) > 0 then\n'
        '        return path of active workspace document\n'
        '    else\n        return "No open workspace"\n    end if\nend tell',
        "active_workspace",
        "[Xcode workspace path unavailable — grant Automation permission]",
    ),
    "antigravity": (
        'tell application "Antigravity"\n'
        '    if (count of windows) > 0 then\n'
        '        return name of front window\n'
        '    else\n        return "Running (no window title accessible)"\n    end if\nend tell',
        "active_window",
        "[Antigravity running — window title requires Accessibility permission or AppleScript support]",
    ),
}


def _scan_all_ide_processes() -> dict[str, list[dict]]:
    """Single psutil pass returning hits for every IDE group."""
    lowered = {env: [n.lower() for n in names] for env, names in _IDE_PROCESS_NAMES.items()}
    results: dict[str, list[dict]] = {env: [] for env in _IDE_PROCESS_NAMES}
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = proc.info.get("name") or ""
            pl = pname.lower()
            for env, names in lowered.items():
                if any(pl == n or pl.startswith(n) for n in names):
                    results[env].append({"pid": proc.info["pid"], "name": pname})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return results


def _scan_processes(names: list[str]) -> list[dict]:
    """Return {pid, name} dicts for processes matching any of names."""
    hits: list[dict] = []
    name_lower = [n.lower() for n in names]
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = proc.info.get("name") or ""
            pl = pname.lower()
            if any(pl == n or pl.startswith(n) for n in name_lower):
                hits.append({"pid": proc.info["pid"], "name": pname})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return hits


def _run_applescript(script: str, timeout: float = 5.0) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"osascript exited {result.returncode}")
    return result.stdout.strip()


def _applescript_safe(script: str, fallback: str = "[AppleScript unavailable]") -> str:
    try:
        return _run_applescript(script)
    except Exception as exc:
        return f"{fallback}: {exc}"


# ---------------------------------------------------------------------------
# Tool: get_dev_context
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Scan running processes for active developer environments (Antigravity IDE, "
        "VS Code, Xcode). Attempts AppleScript to retrieve active workspace/window "
        "title; falls back gracefully if Accessibility permissions are denied."
    )
)
def get_dev_context() -> dict:
    all_procs = _scan_all_ide_processes()
    context = {
        env: {"running": bool(procs), "processes": procs}
        for env, procs in all_procs.items()
    }
    for env, (script, key, fallback) in _IDE_APPLESCRIPT.items():
        if context[env]["running"]:
            context[env][key] = _applescript_safe(script, fallback=fallback)
    return context


# ---------------------------------------------------------------------------
# Tool: get_media_status
# ---------------------------------------------------------------------------

_MEDIA_APPLESCRIPT = """
tell application "{app}"
    set s to player state
    if s is playing then
        set t to name of current track
        set a to artist of current track
        return t & "||" & a & "||playing"
    else if s is paused then
        return "|||| paused"
    else
        return "|||| stopped"
    end if
end tell
"""

# (result_key, process_name, display_name)
_PLAYERS = [
    ("spotify",     "Spotify", "Spotify"),
    ("apple_music", "Music",   "Apple Music"),
]


def _query_player(app_name: str) -> dict:
    raw = _run_applescript(_MEDIA_APPLESCRIPT.format(app=app_name), timeout=4.0)
    parts = raw.split("||")
    if len(parts) >= 3:
        track, artist, state = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if state == "playing" and track:
            return {"app": app_name, "state": "playing", "track": track, "artist": artist}
        return {"app": app_name, "state": state or "stopped"}
    return {"app": app_name, "state": raw or "unknown"}


@mcp.tool(
    description=(
        "Query Spotify and Apple Music for the currently playing track and artist. "
        "Returns player state for each app that is running, plus an 'active' summary "
        "of the first app that is actually playing."
    )
)
def get_media_status() -> dict:
    result: dict = {}
    for key, proc_name, display_name in _PLAYERS:
        if bool(_scan_processes([proc_name])):
            try:
                result[key] = _query_player(proc_name)
            except Exception as exc:
                result[key] = {"app": display_name, "state": "error", "detail": str(exc)}
        else:
            result[key] = {"app": display_name, "state": "not running"}

    for key, _, _ in _PLAYERS:
        if result.get(key, {}).get("state") == "playing":
            result["active"] = result[key]
            return result
    result["active"] = {"state": "nothing playing"}
    return result


# ---------------------------------------------------------------------------
# Tool: get_mac_telemetry
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Return current macOS system telemetry: CPU utilization percentage, "
        "available RAM (GB and % used), and battery level with charging status."
    )
)
def get_mac_telemetry() -> dict:
    telemetry: dict = {}

    try:
        # interval=None: delta since last call — instant, no blocking sleep
        telemetry["cpu_percent"] = psutil.cpu_percent(interval=None)
    except Exception as exc:
        telemetry["cpu_percent"] = f"error: {exc}"

    try:
        vm = psutil.virtual_memory()
        telemetry["memory"] = {
            "total_gb":    round(vm.total / 1024 ** 3, 2),
            "available_gb": round(vm.available / 1024 ** 3, 2),
            "used_percent": vm.percent,
        }
    except Exception as exc:
        telemetry["memory"] = {"error": str(exc)}

    try:
        batt = psutil.sensors_battery()
        if batt is None:
            telemetry["battery"] = {"status": "no battery detected"}
        else:
            if batt.secsleft in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED):
                time_left: str | float = "calculating" if not batt.power_plugged else "unlimited (charging)"
            else:
                time_left = round(batt.secsleft / 60, 1)
            telemetry["battery"] = {
                "percent":          round(batt.percent, 1),
                "charging":         batt.power_plugged,
                "time_left_minutes": time_left,
            }
    except Exception as exc:
        telemetry["battery"] = {"error": str(exc)}

    return telemetry


# ---------------------------------------------------------------------------
# Tool: get_discord_activity
# ---------------------------------------------------------------------------

_DISCORD_USER_ID = "755094519489363979"

_GAME_PROCESSES: dict[str, str] = {
    "steam_osx": "Steam",            "Steam": "Steam",
    "EpicGamesLauncher": "Epic Games Launcher",
    "Battle.net": "Battle.net",      "Blizzard Battle.net": "Battle.net",
    "GOGGalaxy": "GOG Galaxy",
    "LeagueClient": "League of Legends", "League of Legends": "League of Legends",
    "VALORANT": "Valorant",
    "cs2": "Counter-Strike 2",
    "dota2": "Dota 2",
    "Overwatch": "Overwatch 2",
    "Wow": "World of Warcraft",
    "Hearthstone": "Hearthstone",
    "Minecraft": "Minecraft",        "minecraft-launcher": "Minecraft",
    "StardewValley": "Stardew Valley",
    "hollow_knight": "Hollow Knight",
    "Among Us": "Among Us",
    "Cyberpunk2077": "Cyberpunk 2077",
    "RocketLeague": "Rocket League",
    "rpcs3": "RPCS3 (PS3 Emulator)",
    "PCSX2": "PCSX2 (PS2 Emulator)",
    "Ryujinx": "Ryujinx (Switch Emulator)",
    "Dolphin": "Dolphin (GameCube/Wii Emulator)",
    "PPSSPP": "PPSSPP (PSP Emulator)",
    "retroarch": "RetroArch",
    "RemotePlay": "PS Remote Play",
    "GeForceNOW": "GeForce NOW",
    "SteamLink": "Steam Link",
}


def _lanyard_query() -> dict | None:
    try:
        r = _http.get(f"https://api.lanyard.rest/v1/users/{_DISCORD_USER_ID}")
        data = r.json()
        if not data.get("success"):
            return None

        d = data["data"]
        activities = [a for a in d.get("activities", []) if a.get("type") == 0]
        entry: dict = {
            "discord_status":    d.get("discord_status", "unknown"),
            "active_on_mobile":  d.get("active_on_mobile", False),
            "active_on_desktop": d.get("active_on_desktop", False),
        }

        if activities:
            a = activities[0]
            entry["playing"] = a.get("name")
            entry["details"] = a.get("details")
            entry["state"]   = a.get("state")
            if a.get("platform"):
                entry["platform"] = a["platform"]
            ts_start = a.get("timestamps", {}).get("start")
            if ts_start:
                entry["elapsed_minutes"] = round((int(time.time() * 1000) - ts_start) / 60000, 1)
        else:
            entry["playing"] = None

        return entry
    except Exception:
        return None


def _rpc_send(sock: socket.socket, op: int, payload: dict) -> None:
    data = json.dumps(payload).encode()
    sock.send(struct.pack("<II", op, len(data)) + data)


def _rpc_recv(sock: socket.socket) -> dict:
    hdr = b""
    while len(hdr) < 8:
        hdr += sock.recv(8 - len(hdr))
    _, length = struct.unpack("<II", hdr)
    body = b""
    while len(body) < length:
        body += sock.recv(length - len(body))
    return json.loads(body)


def _discord_rpc_query() -> dict | None:
    tmp = os.environ.get("TMPDIR", "/tmp").rstrip("/")
    sock_path = next(
        (f"{tmp}/discord-ipc-{i}" for i in range(10)
         if os.path.exists(f"{tmp}/discord-ipc-{i}")),
        None,
    )
    if not sock_path:
        return None

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    try:
        sock.connect(sock_path)
        _rpc_send(sock, 0, {"v": 1, "client_id": "207646673902501888"})
        ready = _rpc_recv(sock)
        if ready.get("evt") != "READY":
            return None
        user = ready["data"]["user"]
        return {
            "discord_running": True,
            "user":            user.get("username"),
            "note":            "Activity detail requires Lanyard — join discord.gg/lanyard",
        }
    except Exception:
        return None
    finally:
        try:
            sock.close()
        except Exception:
            pass


def _process_scan_games() -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for proc in psutil.process_iter(["name"]):
        try:
            pname = proc.info.get("name") or ""
            game = _GAME_PROCESSES.get(pname)
            if game and game not in seen:
                found.append(game)
                seen.add(game)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found


@mcp.tool(
    description=(
        "Get the user's current Discord activity — what game they're playing, "
        "including PlayStation/console games linked to Discord. "
        "Uses Lanyard API as primary source, falls back to local Discord IPC "
        "and process scanning."
    )
)
def get_discord_activity() -> dict:
    result: dict = {}

    lanyard = _lanyard_query()
    if lanyard:
        result["discord_status"] = lanyard.get("discord_status")
        if lanyard.get("playing"):
            result["source"]  = "lanyard"
            result["playing"] = lanyard["playing"]
            result["details"] = lanyard.get("details")
            result["state"]   = lanyard.get("state")
            if lanyard.get("platform"):
                result["platform"] = lanyard["platform"]
            if lanyard.get("elapsed_minutes"):
                result["elapsed_minutes"] = lanyard["elapsed_minutes"]
            pc_games = _process_scan_games()
            if pc_games:
                result["also_running_locally"] = pc_games
            return result
        result["lanyard_note"] = (
            "Lanyard connected but no game activity — "
            "check Discord Settings → Activity Privacy → "
            "'Display currently running game as status message'"
        )
    else:
        result["lanyard"] = "not available"

    pc_games = _process_scan_games()
    if pc_games:
        result["source"]        = "process_scan"
        result["playing"]       = pc_games[0]
        result["also_detected"] = pc_games[1:]
        result["note"]          = "Detected via local process scan (PC only, no console)"
        return result

    rpc = _discord_rpc_query()
    if rpc:
        result["source"]       = "discord_rpc"
        result["discord_running"] = True
        result["discord_user"] = rpc.get("user")

    result["playing"] = None
    result["note"]    = "No game activity detected"
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if _args.transport in ("sse", "streamable-http"):
        import uvicorn
        asgi_app = mcp.streamable_http_app() if _args.transport == "streamable-http" else mcp.sse_app()
        if _API_KEY:
            asgi_app = _BearerAuth(asgi_app, _API_KEY)
        else:
            import warnings
            warnings.warn("HTTP transport running WITHOUT authentication — set POKE_MCP_API_KEY", stacklevel=1)
        uvicorn.run(asgi_app, host=_args.host, port=_args.port, log_level="info")
    else:
        mcp.run(transport=_args.transport)
