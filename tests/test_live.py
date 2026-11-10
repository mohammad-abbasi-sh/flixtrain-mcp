"""Live tests — hit the real FlixBus shop search API. Cautious: few
requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set FLIXTRAIN_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest
from datetime import date, timedelta

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from flixtrain_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("FLIXTRAIN_SKIP_LIVE") == "1"
TOMORROW = (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")


@pytest.mark.skipif(SKIP, reason="FLIXTRAIN_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_search_cities_live(self):
        out = json.loads(srv.flixtrain_search_cities("Köln", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["total_results"], 1)
        # canonical name is Cologne even for a German query
        self.assertEqual(out["items"][0]["name"], "Cologne")
        self.assertTrue(out["items"][0]["has_train_station"])
        print(f"\nLIVE cities Köln: top={out['items'][0]['name']}")

    def test_search_trains_live(self):
        out = json.loads(srv.flixtrain_search_trains(
            "Berlin", "Hamburg", TOMORROW, limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["train_count"], 1)
        self.assertEqual(out["from_city"], "Berlin")
        self.assertEqual(out["to_city"], "Hamburg")
        first = out["items"][0]
        self.assertEqual(first["operator"], "FlixTrain")
        self.assertIn("Hamburg", first["arrival_station"])
        print(f"\nLIVE trains Berlin->Hamburg {TOMORROW}: "
              f"{out['train_count']} trains, {out['bus_count']} buses — "
              f"first {first['departure_station']} "
              f"{first['departure'][11:16]} -> "
              f"{first['arrival_station']} "
              f"{first['arrival'][11:16]}, {first['price_eur']} EUR")

    def test_search_trains_price_sort_live(self):
        out = json.loads(srv.flixtrain_search_trains(
            "Berlin", "Hamburg", TOMORROW, limit=5, sort="price"))
        self.assertNotIn("error", out)
        prices = [t["price_eur"] for t in out["items"]]
        self.assertEqual(prices, sorted(prices))
