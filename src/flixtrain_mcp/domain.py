"""Domain logic: shape the FlixBus shop search API (used by
flixtrain.de, which redirects to flixbus.com) into compact dicts
(stdlib only).

Data source: https://global.api.flixbus.com/search — the same JSON
API the FlixBus shop uses. Free, no key, no login, but the gateway
requires `Referer: https://shop.flixbus.com/` (without it: 403
"Missing Authentication Token").

Endpoints (verified 2026-11-10):
- GET /search/autocomplete/cities?q=<name>&locale=de — city
  candidates [{id (UUID), name, country, has_train_station, lat/lon,
  legacy_id}]. Note: names are the canonical (English) form — Köln
  comes back as "Cologne" even with locale=de; matching happens
  server-side on the query, so resolving by top hit works.
- GET /search/service/v4/search?from_city_id=<uuid>&to_city_id=<uuid>
  &departure_date=DD.MM.YYYY&products={"adult":1}&currency=EUR
  &locale=de&search_by=cities&include_after_midnight=false —
  {trips: [{date, results: {uid: {...}}}], operators, brands,
  cities, stations}. Each result has legs[] with
  means_of_transport (bus/train), operator_id ("train" = FlixTrain
  GmbH), departure/arrival (date, city_id, station_id), duration,
  price {total, total_with_platform_fee}, available {seats},
  amenities, transfer_type ("Zug" for trains). Station/city names
  come from the response's stations/cities maps.
- Only train legs are exposed (the server is FlixTrain, not
  FlixBus); the bus count is reported for context.
- The v2/trip/details endpoint was probed and does not accept the
  documented uid params (400 "Must provide trip uid") — not used;
  the v4 search already carries times, stations, price and seats.
- The search does not do round trips (return_date is ignored).
"""
from __future__ import annotations

import json
import re
from datetime import datetime

API_BASE = "https://global.api.flixbus.com/search"
FLIXTRAIN_BRAND_ID = "adf3cadd-7991-436c-be53-eb0f9c5ac165"

_CITY_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def validate_query(query: str) -> str:
    q = (query or "").strip()
    if not q:
        raise ValueError("query must not be empty")
    if len(q) > 100:
        raise ValueError("query too long (max 100 characters)")
    return q


def validate_limit(limit: int, maximum: int = 20) -> int:
    if not 1 <= limit <= maximum:
        raise ValueError(
            f"limit out of range: {limit} (expected 1..{maximum})")
    return limit


def validate_date(date: str) -> str:
    """DD.MM.YYYY (the API's format); must be a real calendar date
    and not in the past."""
    d = (date or "").strip()
    try:
        parsed = datetime.strptime(d, "%d.%m.%Y").date()
    except ValueError:
        raise ValueError(
            f"invalid date {date!r} (expected DD.MM.YYYY, e.g. 11.11.2026)"
        ) from None
    if parsed < datetime.now().date():
        raise ValueError(f"date {d} is in the past")
    return d


def validate_sort(sort: str) -> str:
    s = (sort or "departure").strip().lower()
    if s not in ("departure", "price"):
        raise ValueError(
            f"unsupported sort: {sort!r} (use departure or price)")
    return s


def autocomplete_url(query: str) -> str:
    return f"{API_BASE}/autocomplete/cities?q={query}&locale=de"


def search_url(from_id: str, to_id: str, date: str) -> str:
    return (
        f"{API_BASE}/service/v4/search?from_city_id={from_id}"
        f"&to_city_id={to_id}&departure_date={date}"
        "&products=%7B%22adult%22%3A1%7D&currency=EUR&locale=de"
        "&search_by=cities&include_after_midnight=false"
    )


def parse_cities(payload) -> list[dict]:
    """[{id, name, country, has_train_station, lat, lon}] — top
    first (the API's own relevance ranking)."""
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, list):
        raise ValueError("unexpected autocomplete response (not a list)")
    out = []
    for c in payload:
        loc = c.get("location") or {}
        out.append({
            "id": c.get("id", ""),
            "name": c.get("name", ""),
            "country": c.get("country", ""),
            "has_train_station": bool(c.get("has_train_station")),
            "lat": loc.get("lat"),
            "lon": loc.get("lon"),
        })
    return out


def resolve_city(cities: list[dict], query: str) -> dict:
    """Top autocomplete hit (prefer one with a train station when
    the top hit has none and a later hit has one — the train search
    needs a station)."""
    if not cities:
        raise ValueError(
            f"no city found for {query!r} "
            "(try a different spelling, e.g. Cologne for Köln)")
    top = cities[0]
    if top["has_train_station"]:
        return top
    for c in cities[1:]:
        if c["has_train_station"] and c["name"].casefold() == top["name"].casefold():
            return c
    return top


def parse_search(payload) -> dict:
    """{trains: [{departure, departure_station, arrival,
    arrival_station, duration_minutes, price_eur,
    price_incl_fee_eur, seats_available, amenities, operator}],
    bus_count, train_count, from_city, to_city} — trains only,
    sorted by departure time."""
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict) or "trips" not in payload:
        raise ValueError("unexpected search response (no trips)")
    stations = payload.get("stations") or {}
    cities = payload.get("cities") or {}
    trains: list[dict] = []
    bus_count = 0
    from_city = to_city = ""
    for group in payload["trips"]:
        from_city = (cities.get(group.get("departure_city_id", "")) or {}).get("name", "")
        to_city = (cities.get(group.get("arrival_city_id", "")) or {}).get("name", "")
        for _uid, r in (group.get("results") or {}).items():
            legs = r.get("legs") or []
            if not legs:
                continue
            if legs[0].get("means_of_transport") != "train":
                bus_count += 1
                continue
            dep = r.get("departure") or {}
            arr = r.get("arrival") or {}
            dep_station = stations.get(dep.get("station_id", "")) or {}
            arr_station = stations.get(arr.get("station_id", "")) or {}
            dur = r.get("duration") or {}
            price = r.get("price") or {}
            avail = r.get("available") or {}
            trains.append({
                "departure": dep.get("date", ""),
                "departure_station": dep_station.get("name", ""),
                "arrival": arr.get("date", ""),
                "arrival_station": arr_station.get("name", ""),
                "duration_minutes": (dur.get("hours", 0) * 60
                                     + dur.get("minutes", 0)),
                "price_eur": price.get("total"),
                "price_incl_fee_eur": price.get("total_with_platform_fee"),
                "seats_available": avail.get("seats"),
                "amenities": legs[0].get("amenities") or [],
                "operator": "FlixTrain",
            })
    trains.sort(key=lambda t: t["departure"])
    return {
        "trains": trains,
        "train_count": len(trains),
        "bus_count": bus_count,
        "from_city": from_city,
        "to_city": to_city,
    }
