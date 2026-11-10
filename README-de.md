# flixtrain-mcp 🚆

mcp-name: io.github.mohammad-abbasi-sh/flixtrain-mcp

Inoffizieller **nur lesender** MCP-Server für **[global.api.flixbus.com (FlixBus shop search API)](https://shop.flixbus.com)** — FlixTrain-Zeiten & Preise über die FlixBus-Shop-Suche (kostenlos, kein Schlüssel, kein Login): nur Zugverbindungen zwischen deutschen Städten, mit Bahnhöfen, Fahrzeit, Preis und Sitzplatzverfügbarkeit. Kein Schlüssel, keine Anmeldung.

> Gebaut von Mohammad Abbasi als Teil der "Germany MCP factory". Nicht mit global.api.flixbus.com (FlixBus shop search API) verbunden.

## Für KI-Agenten

Zur MCP-Client-Konfiguration hinzufügen (stdio):

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

Oder lokal starten: `python -m flixtrain_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|-------------|
| `flixtrain_search_trains` | FlixTrain-Verbindungen zwischen zwei Städten suchen |
| `flixtrain_search_cities` | Städte nach Namen finden |
| `flixtrain_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## Lizenz

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
