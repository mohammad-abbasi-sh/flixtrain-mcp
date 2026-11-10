# flixtrain-mcp 🚆

mcp-name: io.github.mohammad-abbasi-sh/flixtrain-mcp

Unofficial **read-only** MCP server for **[global.api.flixbus.com (FlixBus shop search API)](https://shop.flixbus.com)** — FlixTrain times & prices from the FlixBus shop search API (free, no key, no login): train-only departures between German cities, with stations, duration, price and seat availability. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory". Not affiliated with global.api.flixbus.com (FlixBus shop search API).

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "flixtrain": {
      "command": "uvx",
      "args": ["flixtrain-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m flixtrain_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `flixtrain_search_trains` | Search FlixTrain-only departures between two cities on a date: times, stations, duration, price & seats — `from_city`, `to_city`, `date` (DD.MM.YYYY), `limit` 1..20, `sort` (departure/price) |
| `flixtrain_search_cities` | Find cities (with train stations) by name for the train search — `query`, `limit` 1..10 |
| `flixtrain_health` | Reachability probe (ok / blocked / error) — one polite request |

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
