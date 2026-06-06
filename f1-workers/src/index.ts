const OPENF1 = "https://api.openf1.org/v1";
const JOLPICA = "https://api.jolpi.ca/ergast/f1";

// ── HTTP helpers ──────────────────────────────────────────────────────────────

async function get(url: string): Promise<unknown> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
}

function openf1(path: string, params: Record<string, unknown> = {}): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) q.set(k, String(v));
  }
  const qs = q.toString();
  return `${OPENF1}/${path}${qs ? `?${qs}` : ""}`;
}

async function resolveSessionKey(sessionKey?: number): Promise<number> {
  if (sessionKey !== undefined) return sessionKey;
  const data = await get(openf1("sessions", { session_key: "latest" })) as Array<{ session_key: number }>;
  return Array.isArray(data) ? data[0].session_key : (data as { session_key: number }).session_key;
}

// ── MCP protocol ──────────────────────────────────────────────────────────────

interface Tool {
  name: string;
  description: string;
  inputSchema: { type: "object"; properties: Record<string, unknown>; required?: string[] };
}

interface MCPRequest {
  jsonrpc: "2.0";
  id: number | string | null;
  method: string;
  params?: Record<string, unknown>;
}

function sse(data: unknown): Response {
  return new Response(`event: message\ndata: ${JSON.stringify(data)}\n\n`, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Access-Control-Allow-Origin": "*",
    },
  });
}

function ok(id: number | string | null, result: unknown): Response {
  return sse({ jsonrpc: "2.0", id, result });
}

function rpcError(id: number | string | null, code: number, message: string): Response {
  return sse({ jsonrpc: "2.0", id, error: { code, message } });
}

// ── Tool definitions ──────────────────────────────────────────────────────────

const TOOLS: Tool[] = [
  {
    name: "get_race_schedule",
    description: "Full F1 race calendar for a given year with country, circuit, and date.",
    inputSchema: { type: "object", properties: { year: { type: "number", default: 2026 } } },
  },
  {
    name: "get_sessions",
    description: "List F1 sessions. session_type: 'Race' | 'Qualifying' | 'Sprint' | 'Practice 1-3'",
    inputSchema: {
      type: "object",
      properties: {
        year: { type: "number" },
        session_type: { type: "string" },
        country_name: { type: "string" },
        circuit_short_name: { type: "string" },
      },
    },
  },
  {
    name: "get_latest_session",
    description: "Currently active or most recently completed session.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get_meetings",
    description: "Grand Prix weekend details: official name, location, circuit, dates.",
    inputSchema: { type: "object", properties: { year: { type: "number" }, country_name: { type: "string" } } },
  },
  {
    name: "get_drivers",
    description: "All drivers with number, abbreviation, team, and headshot URL. Defaults to latest session.",
    inputSchema: { type: "object", properties: { session_key: { type: "number" } } },
  },
  {
    name: "get_positions",
    description: "Live race standings updated every 4 seconds.",
    inputSchema: { type: "object", properties: { session_key: { type: "number" }, driver_number: { type: "number" } } },
  },
  {
    name: "get_intervals",
    description: "Gap to leader and gap ahead, updated every 4 seconds.",
    inputSchema: { type: "object", properties: { session_key: { type: "number" }, driver_number: { type: "number" } } },
  },
  {
    name: "get_race_control",
    description: "Race control messages: safety car, VSC, flags, DRS, penalties.",
    inputSchema: { type: "object", properties: { session_key: { type: "number" } } },
  },
  {
    name: "get_laps",
    description: "Lap times with sector splits, speed trap, and tyre compound.",
    inputSchema: {
      type: "object",
      properties: {
        session_key: { type: "number" },
        driver_number: { type: "number" },
        lap_number: { type: "number" },
      },
    },
  },
  {
    name: "get_stints",
    description: "Tyre stint data: compound, start/end lap, new or used tyre.",
    inputSchema: { type: "object", properties: { session_key: { type: "number" }, driver_number: { type: "number" } } },
  },
  {
    name: "get_pit_stops",
    description: "Pit stop records: lap number, pit lane duration, total stop duration.",
    inputSchema: { type: "object", properties: { session_key: { type: "number" }, driver_number: { type: "number" } } },
  },
  {
    name: "get_telemetry",
    description: "Car telemetry at 3.7 Hz: speed, throttle, brake, RPM, gear, DRS. Always specify lap_number.",
    inputSchema: {
      type: "object",
      properties: {
        session_key: { type: "number" },
        driver_number: { type: "number" },
        lap_number: { type: "number" },
      },
      required: ["session_key", "driver_number"],
    },
  },
  {
    name: "get_location",
    description: "GPS coordinates at 3.7 Hz: x/y on track map and z altitude. Always specify lap_number.",
    inputSchema: {
      type: "object",
      properties: {
        session_key: { type: "number" },
        driver_number: { type: "number" },
        lap_number: { type: "number" },
      },
      required: ["session_key", "driver_number"],
    },
  },
  {
    name: "get_weather",
    description: "Track and air conditions: temperature, humidity, wind speed/direction, rainfall.",
    inputSchema: { type: "object", properties: { session_key: { type: "number" } } },
  },
  {
    name: "get_team_radio",
    description: "Team radio recordings with audio URL and transcript where available.",
    inputSchema: { type: "object", properties: { session_key: { type: "number" }, driver_number: { type: "number" } } },
  },
  {
    name: "get_driver_standings",
    description: "Driver championship standings: points, wins, and constructor. Omit round for latest.",
    inputSchema: { type: "object", properties: { year: { type: "number", default: 2026 }, round: { type: "number" } } },
  },
  {
    name: "get_constructor_standings",
    description: "Constructor championship standings: points and wins per team. Omit round for latest.",
    inputSchema: { type: "object", properties: { year: { type: "number", default: 2026 }, round: { type: "number" } } },
  },
  {
    name: "get_race_results",
    description: "Official race results with positions, points, fastest lap. Omit round for most recent.",
    inputSchema: { type: "object", properties: { year: { type: "number", default: 2026 }, round: { type: "number" } } },
  },
];

// ── Tool handlers ─────────────────────────────────────────────────────────────

type Args = Record<string, unknown>;

async function callTool(name: string, args: Args): Promise<unknown> {
  switch (name) {
    case "get_race_schedule": {
      const year = (args.year as number) ?? 2026;
      const data = await get(openf1("sessions", { year, session_type: "Race" })) as Array<Record<string, unknown>>;
      return data.map((s, i) => ({
        round: i + 1,
        country: s.country_name,
        circuit: s.circuit_short_name,
        date_start: s.date_start,
        session_key: s.session_key,
      }));
    }
    case "get_sessions":
      return get(openf1("sessions", args));
    case "get_latest_session": {
      const data = await get(openf1("sessions", { session_key: "latest" })) as unknown[];
      return Array.isArray(data) ? data[0] : data;
    }
    case "get_meetings":
      return get(openf1("meetings", args));
    case "get_drivers": {
      const key = await resolveSessionKey(args.session_key as number | undefined);
      return get(openf1("drivers", { session_key: key }));
    }
    case "get_positions": {
      const key = await resolveSessionKey(args.session_key as number | undefined);
      return get(openf1("position", { session_key: key, driver_number: args.driver_number }));
    }
    case "get_intervals": {
      const key = await resolveSessionKey(args.session_key as number | undefined);
      return get(openf1("intervals", { session_key: key, driver_number: args.driver_number }));
    }
    case "get_race_control": {
      const key = await resolveSessionKey(args.session_key as number | undefined);
      return get(openf1("race_control", { session_key: key }));
    }
    case "get_laps": {
      const key = await resolveSessionKey(args.session_key as number | undefined);
      return get(openf1("laps", { session_key: key, driver_number: args.driver_number, lap_number: args.lap_number }));
    }
    case "get_stints": {
      const key = await resolveSessionKey(args.session_key as number | undefined);
      return get(openf1("stints", { session_key: key, driver_number: args.driver_number }));
    }
    case "get_pit_stops": {
      const key = await resolveSessionKey(args.session_key as number | undefined);
      return get(openf1("pit", { session_key: key, driver_number: args.driver_number }));
    }
    case "get_telemetry":
      return get(openf1("car_data", { session_key: args.session_key, driver_number: args.driver_number, lap_number: args.lap_number }));
    case "get_location":
      return get(openf1("location", { session_key: args.session_key, driver_number: args.driver_number, lap_number: args.lap_number }));
    case "get_weather": {
      const key = await resolveSessionKey(args.session_key as number | undefined);
      return get(openf1("weather", { session_key: key }));
    }
    case "get_team_radio": {
      const key = await resolveSessionKey(args.session_key as number | undefined);
      return get(openf1("team_radio", { session_key: key, driver_number: args.driver_number }));
    }
    case "get_driver_standings": {
      const year = (args.year as number) ?? 2026;
      const path = args.round ? `${year}/${args.round}/driverStandings.json` : `${year}/driverStandings.json`;
      const data = await get(`${JOLPICA}/${path}`) as { MRData: { StandingsTable: { StandingsLists: Array<{ DriverStandings: Array<Record<string, unknown>> }> } } };
      const lists = data.MRData.StandingsTable.StandingsLists;
      if (!lists.length) return [];
      return lists[0].DriverStandings.map((s) => ({
        position: Number(s.position),
        driver: `${(s.Driver as Record<string, string>).givenName} ${(s.Driver as Record<string, string>).familyName}`,
        code: (s.Driver as Record<string, string>).code,
        team: (s.Constructors as Array<Record<string, string>>)[0]?.name,
        points: Number(s.points),
        wins: Number(s.wins),
      }));
    }
    case "get_constructor_standings": {
      const year = (args.year as number) ?? 2026;
      const path = args.round ? `${year}/${args.round}/constructorStandings.json` : `${year}/constructorStandings.json`;
      const data = await get(`${JOLPICA}/${path}`) as { MRData: { StandingsTable: { StandingsLists: Array<{ ConstructorStandings: Array<Record<string, unknown>> }> } } };
      const lists = data.MRData.StandingsTable.StandingsLists;
      if (!lists.length) return [];
      return lists[0].ConstructorStandings.map((s) => ({
        position: Number(s.position),
        team: (s.Constructor as Record<string, string>).name,
        nationality: (s.Constructor as Record<string, string>).nationality,
        points: Number(s.points),
        wins: Number(s.wins),
      }));
    }
    case "get_race_results": {
      const year = (args.year as number) ?? 2026;
      const path = args.round ? `${year}/${args.round}/results.json` : `${year}/last/results.json`;
      const data = await get(`${JOLPICA}/${path}`) as { MRData: { RaceTable: { Races: Array<Record<string, unknown>> } } };
      const races = data.MRData.RaceTable.Races;
      if (!races.length) return [];
      const race = races[0];
      return {
        race: race.raceName,
        circuit: (race.Circuit as Record<string, string>).circuitName,
        date: race.date,
        results: (race.Results as Array<Record<string, unknown>>).map((r) => ({
          position: Number(r.position),
          driver: `${(r.Driver as Record<string, string>).givenName} ${(r.Driver as Record<string, string>).familyName}`,
          team: (r.Constructor as Record<string, string>).name,
          grid: Number(r.grid),
          laps: Number(r.laps),
          status: r.status,
          points: Number(r.points),
          fastest_lap: (r.FastestLap as Record<string, Record<string, string>> | undefined)?.Time?.time,
        })),
      };
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

// ── Request handler ───────────────────────────────────────────────────────────

export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Accept, mcp-session-id",
        },
      });
    }

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
          const toolName = (params as { name: string }).name;
          const args = ((params as { arguments?: Args }).arguments) ?? {};
          const result = await callTool(toolName, args);
          return ok(id, {
            content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
          });
        }

        default:
          return rpcError(id, -32601, `Method not found: ${method}`);
      }
    } catch (e) {
      return rpcError(id, -32603, e instanceof Error ? e.message : "Internal error");
    }
  },
};
