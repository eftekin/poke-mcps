# F1 Live Data MCP

Formula 1 gerçek zamanlı veri sunucusu. [OpenF1 API](https://openf1.org) kullanır — ücretsiz, kayıt gerekmez.

## Araçlar

| Tool | Açıklama |
|------|----------|
| `get_race_schedule` | Sezon takvimi |
| `get_latest_session` | Aktif/son oturum |
| `get_sessions` | Oturumları filtrele (yıl, tip, ülke) |
| `get_drivers` | Sürücü listesi |
| `get_positions` | Anlık sıralama (4sn güncelleme) |
| `get_intervals` | Araç arası süre farkları |
| `get_laps` | Tur süreleri ve sektör zamanları |
| `get_stints` | Lastik stratejisi |
| `get_pit_stops` | Pit stop verileri |
| `get_weather` | Hava durumu |
| `get_race_control` | Safety car, bayraklar, cezalar |
| `get_team_radio` | Telsiz mesajları |
| `get_telemetry` | Araç telemetri (hız, gaz, fren, vites) |

## Deploy (Render.com — Ücretsiz)

1. [render.com](https://render.com) → New → Web Service
2. Bu repoyu bağlayın, **Root Directory** olarak `f1` girin
3. **Build**: `pip install -r requirements.txt`
4. **Start**: `fastmcp run src/server.py:mcp --transport streamable-http --host 0.0.0.0 --port $PORT`
5. **Instance Type**: Free

## Poke'a Ekleme

Settings → Integrations → Add Custom MCP Server

- **URL**: `https://<render-url>/mcp`
- Auth: None
