const OPENF1 = "https://api.openf1.org/v1";
const JOLPICA = "https://api.jolpi.ca/ergast/f1";

// ── HTTP helpers ──────────────────────────────────────────────────────────────

async function get<T = unknown>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json() as Promise<T>;
}

function openf1(path: string, params: Record<string, unknown> = {}): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) q.set(k, String(v));
  }
  const qs = q.toString();
  return `${OPENF1}/${path}${qs ? `?${qs}` : ""}`;
}

function jolpicaPath(resource: string, year: number, round?: number): string {
  return round ? `${year}/${round}/${resource}.json` : `${year}/${resource}.json`;
}

async function resolveSessionKey(sessionKey?: number): Promise<number> {
  if (sessionKey !== undefined) return sessionKey;
  const data = await get<Array<{ session_key: number }>>(openf1("sessions", { session_key: "latest" }));
  return Array.isArray(data) ? data[0].session_key : data.session_key;
}

// ── Typed API shapes ──────────────────────────────────────────────────────────

interface JolpicaDriver {
  position: string; points: string; wins: string;
  Driver: { givenName: string; familyName: string; code: string };
  Constructors: Array<{ name: string }>;
}
interface JolpicaConstructor {
  position: string; points: string; wins: string;
  Constructor: { name: string; nationality: string };
}
interface JolpicaRaceResult {
  position: string; grid: string; laps: string; status: string; points: string;
  Driver: { givenName: string; familyName: string };
  Constructor: { name: string };
  FastestLap?: { Time: { time: string } };
}
interface JolpicaRace {
  raceName: string; date: string;
  Circuit: { circuitName: string };
  Results: JolpicaRaceResult[];
}
interface JolpicaStandings<T> {
  MRData: { StandingsTable: { StandingsLists: Array<T> } };
}
interface JolpicaResults {
  MRData: { RaceTable: { Races: JolpicaRace[] } };
}

// ── MCP protocol ──────────────────────────────────────────────────────────────

type Args = Record<string, unknown>;

interface ToolSchema {
  name: string;
  description: string;
  inputSchema: { type: "object"; properties: Record<string, unknown>; required?: string[] };
}

interface ToolDef {
  schema: ToolSchema;
  handler: (args: Args) => Promise<unknown>;
}

interface MCPRequest {
  jsonrpc: "2.0";
  id: number | string | null;
  method: string;
  params?: Record<string, unknown>;
}

const SSE_HEADERS = {
  "Content-Type": "text/event-stream",
  "Cache-Control": "no-cache",
  "Access-Control-Allow-Origin": "*",
};

function sse(data: unknown): Response {
  return new Response(`event: message\ndata: ${JSON.stringify(data)}\n\n`, { headers: SSE_HEADERS });
}
function ok(id: number | string | null, result: unknown): Response {
  return sse({ jsonrpc: "2.0", id, result });
}
function rpcError(id: number | string | null, code: number, message: string): Response {
  return sse({ jsonrpc: "2.0", id, error: { code, message } });
}

// ── Schema helpers ────────────────────────────────────────────────────────────

const SESSION_KEY_PROP = { session_key: { type: "number" } };
const DRIVER_PROP = { driver_number: { type: "number" } };
const SESSION_DRIVER_PROPS = { ...SESSION_KEY_PROP, ...DRIVER_PROP };
const YEAR_ROUND_PROPS = { year: { type: "number", default: 2026 }, round: { type: "number" } };

// ── Session-aware OpenF1 helper ───────────────────────────────────────────────

async function sessionTool(endpoint: string, args: Args): Promise<unknown> {
  const key = await resolveSessionKey(args.session_key as number | undefined);
  return get(openf1(endpoint, { session_key: key, driver_number: args.driver_number, lap_number: args.lap_number }));
}

// ── Tool registry ─────────────────────────────────────────────────────────────

const TOOL_MAP: Record<string, ToolDef> = {
  // Schedule & Sessions
  get_race_schedule: {
    schema: {
      name: "get_race_schedule",
      description: "Full F1 race calendar for a given year with country, circuit, and date.",
      inputSchema: { type: "object", properties: { year: { type: "number", default: 2026 } } },
    },
    handler: async ({ year }) => {
      const data = await get<Array<Record<string, unknown>>>(openf1("sessions", { year: year ?? 2026, session_type: "Race" }));
      return data.map((s, i) => ({ round: i + 1, country: s.country_name, circuit: s.circuit_short_name, date_start: s.date_start, session_key: s.session_key }));
    },
  },
  get_sessions: {
    schema: {
      name: "get_sessions",
      description: "List F1 sessions. session_type: 'Race' | 'Qualifying' | 'Sprint' | 'Practice 1-3'",
      inputSchema: { type: "object", properties: { year: { type: "number" }, session_type: { type: "string" }, country_name: { type: "string" }, circuit_short_name: { type: "string" } } },
    },
    handler: (args) => get(openf1("sessions", args)),
  },
  get_latest_session: {
    schema: {
      name: "get_latest_session",
      description: "Currently active or most recently completed session.",
      inputSchema: { type: "object", properties: {} },
    },
    handler: async () => {
      const data = await get<unknown[]>(openf1("sessions", { session_key: "latest" }));
      return Array.isArray(data) ? data[0] : data;
    },
  },
  get_meetings: {
    schema: {
      name: "get_meetings",
      description: "Grand Prix weekend details: official name, location, circuit, dates.",
      inputSchema: { type: "object", properties: { year: { type: "number" }, country_name: { type: "string" } } },
    },
    handler: (args) => get(openf1("meetings", args)),
  },

  // Drivers
  get_drivers: {
    schema: {
      name: "get_drivers",
      description: "All drivers with number, abbreviation, team, and headshot URL. Defaults to latest session.",
      inputSchema: { type: "object", properties: SESSION_KEY_PROP },
    },
    handler: (args) => sessionTool("drivers", args),
  },

  // Live Timing
  get_positions: {
    schema: {
      name: "get_positions",
      description: "Live race standings updated every 4 seconds.",
      inputSchema: { type: "object", properties: SESSION_DRIVER_PROPS },
    },
    handler: (args) => sessionTool("position", args),
  },
  get_intervals: {
    schema: {
      name: "get_intervals",
      description: "Gap to leader and gap ahead, updated every 4 seconds.",
      inputSchema: { type: "object", properties: SESSION_DRIVER_PROPS },
    },
    handler: (args) => sessionTool("intervals", args),
  },
  get_race_control: {
    schema: {
      name: "get_race_control",
      description: "Race control messages: safety car, VSC, flags, DRS, penalties.",
      inputSchema: { type: "object", properties: SESSION_KEY_PROP },
    },
    handler: (args) => sessionTool("race_control", args),
  },

  // Laps & Strategy
  get_laps: {
    schema: {
      name: "get_laps",
      description: "Lap times with sector splits, speed trap, and tyre compound.",
      inputSchema: { type: "object", properties: { ...SESSION_DRIVER_PROPS, lap_number: { type: "number" } } },
    },
    handler: (args) => sessionTool("laps", args),
  },
  get_stints: {
    schema: {
      name: "get_stints",
      description: "Tyre stint data: compound, start/end lap, new or used tyre.",
      inputSchema: { type: "object", properties: SESSION_DRIVER_PROPS },
    },
    handler: (args) => sessionTool("stints", args),
  },
  get_pit_stops: {
    schema: {
      name: "get_pit_stops",
      description: "Pit stop records: lap number, pit lane duration, total stop duration.",
      inputSchema: { type: "object", properties: SESSION_DRIVER_PROPS },
    },
    handler: (args) => sessionTool("pit", args),
  },

  // Car Data
  get_telemetry: {
    schema: {
      name: "get_telemetry",
      description: "Car telemetry at 3.7 Hz: speed, throttle, brake, RPM, gear, DRS. Always specify lap_number.",
      inputSchema: { type: "object", properties: { ...SESSION_DRIVER_PROPS, lap_number: { type: "number" } }, required: ["session_key", "driver_number"] },
    },
    handler: ({ session_key, driver_number, lap_number }) =>
      get(openf1("car_data", { session_key, driver_number, lap_number })),
  },
  get_location: {
    schema: {
      name: "get_location",
      description: "GPS coordinates at 3.7 Hz: x/y on track map and z altitude. Always specify lap_number.",
      inputSchema: { type: "object", properties: { ...SESSION_DRIVER_PROPS, lap_number: { type: "number" } }, required: ["session_key", "driver_number"] },
    },
    handler: ({ session_key, driver_number, lap_number }) =>
      get(openf1("location", { session_key, driver_number, lap_number })),
  },

  // Conditions & Radio
  get_weather: {
    schema: {
      name: "get_weather",
      description: "Track and air conditions: temperature, humidity, wind speed/direction, rainfall.",
      inputSchema: { type: "object", properties: SESSION_KEY_PROP },
    },
    handler: (args) => sessionTool("weather", args),
  },
  get_team_radio: {
    schema: {
      name: "get_team_radio",
      description: "Team radio recordings with audio URL and transcript where available.",
      inputSchema: { type: "object", properties: SESSION_DRIVER_PROPS },
    },
    handler: (args) => sessionTool("team_radio", args),
  },

  // Championship
  get_driver_standings: {
    schema: {
      name: "get_driver_standings",
      description: "Driver championship standings: points, wins, and constructor. Omit round for latest.",
      inputSchema: { type: "object", properties: YEAR_ROUND_PROPS },
    },
    handler: async ({ year, round }) => {
      const data = await get<JolpicaStandings<{ DriverStandings: JolpicaDriver[] }>>(`${JOLPICA}/${jolpicaPath("driverStandings", (year as number) ?? 2026, round as number | undefined)}`);
      const list = data.MRData.StandingsTable.StandingsLists[0];
      if (!list) return [];
      return list.DriverStandings.map((s) => ({
        position: Number(s.position),
        driver: `${s.Driver.givenName} ${s.Driver.familyName}`,
        code: s.Driver.code,
        team: s.Constructors[0]?.name,
        points: Number(s.points),
        wins: Number(s.wins),
      }));
    },
  },
  get_constructor_standings: {
    schema: {
      name: "get_constructor_standings",
      description: "Constructor championship standings: points and wins per team. Omit round for latest.",
      inputSchema: { type: "object", properties: YEAR_ROUND_PROPS },
    },
    handler: async ({ year, round }) => {
      const data = await get<JolpicaStandings<{ ConstructorStandings: JolpicaConstructor[] }>>(`${JOLPICA}/${jolpicaPath("constructorStandings", (year as number) ?? 2026, round as number | undefined)}`);
      const list = data.MRData.StandingsTable.StandingsLists[0];
      if (!list) return [];
      return list.ConstructorStandings.map((s) => ({
        position: Number(s.position),
        team: s.Constructor.name,
        nationality: s.Constructor.nationality,
        points: Number(s.points),
        wins: Number(s.wins),
      }));
    },
  },
  get_race_results: {
    schema: {
      name: "get_race_results",
      description: "Official race results with positions, points, fastest lap. Omit round for most recent.",
      inputSchema: { type: "object", properties: YEAR_ROUND_PROPS },
    },
    handler: async ({ year, round }) => {
      const y = (year as number) ?? 2026;
      const path = round ? jolpicaPath("results", y, round as number) : `${y}/last/results.json`;
      const data = await get<JolpicaResults>(`${JOLPICA}/${path}`);
      const race = data.MRData.RaceTable.Races[0];
      if (!race) return [];
      return {
        race: race.raceName,
        circuit: race.Circuit.circuitName,
        date: race.date,
        results: race.Results.map((r) => ({
          position: Number(r.position),
          driver: `${r.Driver.givenName} ${r.Driver.familyName}`,
          team: r.Constructor.name,
          grid: Number(r.grid),
          laps: Number(r.laps),
          status: r.status,
          points: Number(r.points),
          fastest_lap: r.FastestLap?.Time?.time,
        })),
      };
    },
  },
};

const TOOLS = Object.values(TOOL_MAP).map((t) => t.schema);

// ── Request handler ───────────────────────────────────────────────────────────

export default {
  async fetch(request: Request): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Accept, mcp-session-id",
        },
      });
    }

    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname !== "/mcp") {
      return new Response("Not Found", { status: 404 });
    }

    let body: MCPRequest;
    try {
      body = await request.json() as MCPRequest;
    } catch {
      return rpcError(null, -32700, "Parse error");
    }

    const { id, method, params } = body;

    try {
      switch (method) {
        case "initialize":
          return ok(id, {
            protocolVersion: "2024-11-05",
            capabilities: { tools: { listChanged: false } },
            serverInfo: { name: "F1 Live Data", version: "1.0.0" },
          });
        case "notifications/initialized":
          return new Response(null, { status: 204 });
        case "tools/list":
          return ok(id, { tools: TOOLS });
        case "tools/call": {
          const name = (params as { name: string }).name;
          const args = ((params as { arguments?: Args }).arguments) ?? {};
          const tool = TOOL_MAP[name];
          if (!tool) return rpcError(id, -32601, `Unknown tool: ${name}`);
          const result = await tool.handler(args);
          return ok(id, { content: [{ type: "text", text: JSON.stringify(result) }] });
        }
        default:
          return rpcError(id, -32601, `Method not found: ${method}`);
      }
    } catch (e) {
      return rpcError(id, -32603, e instanceof Error ? e.message : "Internal error");
    }
  },
};
