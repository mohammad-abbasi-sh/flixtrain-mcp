"""MCP server: unofficial read-only access to FlixTrain departures
via the FlixBus shop search API (flixtrain.de redirects to
flixbus.com; the shop API serves both). No key, no login — but the
gateway requires the shop as Referer (see http.py). NOTE: only train
legs are exposed (operator FlixTrain GmbH); bus results on the same
route are counted, not listed. City names resolve through the
autocomplete endpoint (top hit; Köln comes back as "Cologne" — the
API's canonical name). Dates are DD.MM.YYYY, one-way only (the API
ignores return dates)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for FlixTrain departures via the \
FlixBus shop search API (no key, no login): search train-only \
departures between two cities on a date (times, stations, duration, \
price, seats), and find cities by name. NOTE: only FlixTrain legs \
are listed (buses on the same route are counted, not shown); city \
names resolve through autocomplete — Köln is returned as "Cologne" \
(the API's canonical name). Dates are DD.MM.YYYY, one-way only. \
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir \
· https://mabbasi.ir — Germany MCP factory.\
"""

_SOURCE = "global.api.flixbus.com"
_DISCLAIMER = ("Unofficial read-only data from the FlixBus shop search "
               "API (FlixTrain); verify on the site before acting on it.")


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("flixtrain-mcp", instructions=INSTRUCTIONS)


def _resolve_city(query: str) -> dict:
    cities = _dom.parse_cities(
        _http.fetch_text(_dom.autocomplete_url(quote(query))))
    return _dom.resolve_city(cities, query)


@mcp.tool()
def flixtrain_search_trains(from_city: str, to_city: str, date: str,
                            limit: int = 10,
                            sort: str = "departure") -> str:
    """Search FlixTrain-only departures between two cities on a date.
    from_city / to_city: city names, e.g. Berlin, Hamburg, Köln
    (Cologne). date: DD.MM.YYYY, e.g. 11.11.2026. limit: 1..20
    (default 10). sort: departure (default) or price."""
    try:
        lim = _dom.validate_limit(limit)
        s = _dom.validate_sort(sort)
        d = _dom.validate_date(date)
        origin = _resolve_city(_dom.validate_query(from_city))
        dest = _resolve_city(_dom.validate_query(to_city))
        if origin["id"] == dest["id"]:
            raise ValueError("from_city and to_city resolve to the same city")
        out = _dom.parse_search(_http.fetch_text(
            _dom.search_url(origin["id"], dest["id"], d)))
        trains = out["trains"]
        if s == "price":
            trains = sorted(trains, key=lambda t: (
                t["price_eur"] is None, t["price_eur"] or 0))
    except (_http.FlixtrainMcpError, ValueError) as e:
        return _err(e)
    return _ok({
        "from_city": origin["name"],
        "to_city": dest["name"],
        "date": d,
        "sort": s,
        "train_count": out["train_count"],
        "bus_count": out["bus_count"],
        "note": (f"{out['bus_count']} bus departures on this route are "
                 "not listed (trains only).") if out["bus_count"] else "",
        "count": min(lim, len(trains)),
        "items": trains[:lim],
    })


@mcp.tool()
def flixtrain_search_cities(query: str, limit: int = 10) -> str:
    """Find cities by name (with train-station flag) for the train
    search. query: e.g. Berlin, Köln, München. limit: 1..10
    (default 10)."""
    try:
        q = _dom.validate_query(query)
        lim = _dom.validate_limit(limit, maximum=10)
        cities = _dom.parse_cities(
            _http.fetch_text(_dom.autocomplete_url(quote(q))))
    except (_http.FlixtrainMcpError, ValueError) as e:
        return _err(e)
    return _ok({"query": q, "total_results": len(cities),
                "count": min(lim, len(cities)), "items": cities[:lim]})


@mcp.tool()
def flixtrain_health() -> str:
    """Check whether the FlixBus search API is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
