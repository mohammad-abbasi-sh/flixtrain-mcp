"""Offline tests — parse real captured FlixBus shop search API
responses (2026-11-10), no network."""
import json
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from flixtrain_mcp import domain as dom
from flixtrain_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


class TestValidation(unittest.TestCase):
    def test_query_and_limit(self):
        self.assertEqual(dom.validate_query("  Berlin "), "Berlin")
        with self.assertRaises(ValueError):
            dom.validate_query("")
        self.assertEqual(dom.validate_limit(10), 10)
        with self.assertRaises(ValueError):
            dom.validate_limit(21)

    def test_date(self):
        self.assertEqual(dom.validate_date("11.11.2026"), "11.11.2026")
        for bad in ["2026-11-11", "11/11/2026", "32.11.2026",
                    "01.01.2020"]:
            with self.assertRaises(ValueError, msg=bad):
                dom.validate_date(bad)

    def test_sort(self):
        self.assertEqual(dom.validate_sort("departure"), "departure")
        self.assertEqual(dom.validate_sort("PRICE"), "price")
        with self.assertRaises(ValueError):
            dom.validate_sort("cheapest")


class TestCities(unittest.TestCase):
    def test_berlin(self):
        cities = dom.parse_cities(_read("autocomplete-berlin.json"))
        self.assertEqual(len(cities), 8)
        self.assertEqual(cities[0], {
            "id": "40d8f682-8646-11e6-9066-549f350fcb0c",
            "name": "Berlin", "country": "de",
            "has_train_station": True,
            "lat": 52.525016, "lon": 13.369474})
        self.assertEqual(dom.resolve_city(cities, "Berlin")["name"],
                         "Berlin")

    def test_koeln_is_cologne(self):
        # The API returns the canonical English name even for a
        # German query; the top hit is still the right city.
        cities = dom.parse_cities(_read("autocomplete-koeln.json"))
        self.assertEqual(cities[0]["name"], "Cologne")
        self.assertTrue(cities[0]["has_train_station"])
        self.assertEqual(dom.resolve_city(cities, "Köln")["name"],
                         "Cologne")

    def test_resolve_empty(self):
        with self.assertRaises(ValueError):
            dom.resolve_city([], "Xyzqweabc")


class TestSearchBerlinHamburg(unittest.TestCase):
    def setUp(self):
        self.out = dom.parse_search(
            _read("search-berlin-hamburg.json"))

    def test_counts(self):
        self.assertEqual(self.out["train_count"], 9)
        self.assertEqual(self.out["bus_count"], 10)
        self.assertEqual(self.out["from_city"], "Berlin")
        self.assertEqual(self.out["to_city"], "Hamburg")

    def test_first_train(self):
        self.assertEqual(self.out["trains"][0], {
            "departure": "2026-11-11T09:55:00+01:00",
            "departure_station": "Berlin Südkreuz",
            "arrival": "2026-11-11T12:21:00+01:00",
            "arrival_station": "Hamburg Hbf",
            "duration_minutes": 146,
            "price_eur": 16.49,
            "price_incl_fee_eur": 17.48,
            "seats_available": 187,
            "amenities": ["WIFI", "POWER_SOCKETS"],
            "operator": "FlixTrain"})

    def test_all_trains(self):
        for t in self.out["trains"]:
            self.assertEqual(t["operator"], "FlixTrain")
            self.assertEqual(t["arrival_station"], "Hamburg Hbf")
            self.assertIsInstance(t["price_eur"], float)

    def test_sorted_by_departure(self):
        deps = [t["departure"] for t in self.out["trains"]]
        self.assertEqual(deps, sorted(deps))


class TestSearchHamburgKoeln(unittest.TestCase):
    def test_counts_and_cheapest(self):
        out = dom.parse_search(_read("search-hamburg-koeln.json"))
        self.assertEqual(out["train_count"], 9)
        self.assertEqual(out["bus_count"], 6)
        cheapest = min(out["trains"], key=lambda t: t["price_eur"])
        self.assertEqual(cheapest["price_eur"], 27.49)
        self.assertEqual(cheapest["departure_station"], "Hamburg Hbf")
        self.assertEqual(cheapest["arrival_station"], "Köln Hbf")


class TestServerWiring(unittest.TestCase):
    def _fetch(self, url):
        if "autocomplete" in url:
            if "q=Berlin" in url:
                return _read("autocomplete-berlin.json")
            if "q=Hamburg" in url:
                return _read("autocomplete-hamburg.json")
        if "v4/search" in url:
            return _read("search-berlin-hamburg.json")
        raise AssertionError(f"unexpected URL: {url}")

    def test_search_trains_uses_fixtures(self):
        with mock.patch("flixtrain_mcp.server._http.fetch_text",
                        side_effect=self._fetch):
            out = json.loads(srv.flixtrain_search_trains(
                "Berlin", "Hamburg", "11.11.2026", limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["source"], "global.api.flixbus.com")
        self.assertEqual(out["from_city"], "Berlin")
        self.assertEqual(out["to_city"], "Hamburg")
        self.assertEqual(out["train_count"], 9)
        self.assertEqual(out["bus_count"], 10)
        self.assertEqual(out["count"], 3)
        self.assertEqual(out["items"][0]["departure_station"],
                         "Berlin Südkreuz")

    def test_search_trains_sort_price(self):
        with mock.patch("flixtrain_mcp.server._http.fetch_text",
                        side_effect=self._fetch):
            out = json.loads(srv.flixtrain_search_trains(
                "Berlin", "Hamburg", "11.11.2026", sort="price"))
        prices = [t["price_eur"] for t in out["items"]]
        self.assertEqual(prices, sorted(prices))

    def test_search_cities_uses_fixture(self):
        with mock.patch("flixtrain_mcp.server._http.fetch_text",
                        return_value=_read("autocomplete-berlin.json")):
            out = json.loads(srv.flixtrain_search_cities("Berlin"))
        self.assertEqual(out["total_results"], 8)
        self.assertEqual(out["items"][0]["name"], "Berlin")

    def test_same_city_rejected(self):
        with mock.patch("flixtrain_mcp.server._http.fetch_text",
                        side_effect=self._fetch):
            out = json.loads(srv.flixtrain_search_trains(
                "Berlin", "Berlin", "11.11.2026"))
        self.assertIn("error", out)

    def test_invalid_date(self):
        out = json.loads(srv.flixtrain_search_trains(
            "Berlin", "Hamburg", "2026-11-11"))
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
