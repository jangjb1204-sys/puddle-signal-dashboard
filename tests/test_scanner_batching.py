import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

import puddle_rsi_signal_scanner as scanner


class BatchDownloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old_cache_dir = scanner.CACHE_DIR
        self.old_cache_max_hours = scanner.CACHE_MAX_HOURS
        self.old_refresh_cache = scanner.REFRESH_CACHE
        self.old_request_pause = scanner.YF_REQUEST_PAUSE_SECONDS
        scanner.CACHE_DIR = Path(self.tmp.name)
        scanner.CACHE_MAX_HOURS = 0.0
        scanner.REFRESH_CACHE = False
        scanner.YF_REQUEST_PAUSE_SECONDS = 0.0

    def tearDown(self):
        scanner.CACHE_DIR = self.old_cache_dir
        scanner.CACHE_MAX_HOURS = self.old_cache_max_hours
        scanner.REFRESH_CACHE = self.old_refresh_cache
        scanner.YF_REQUEST_PAUSE_SECONDS = self.old_request_pause

    def test_fetch_batch_stock_data_downloads_uncached_tickers_together(self):
        calls = []

        def fake_download(tickers, period, group_by, auto_adjust, progress, threads):
            calls.append(tuple(tickers))
            dates = pd.date_range("2026-06-22", periods=2)
            columns = pd.MultiIndex.from_product([tickers, ["Open", "High", "Low", "Close", "Volume"]])
            values = []
            for row_index in range(2):
                row = []
                for offset, _ticker in enumerate(tickers):
                    base = 100 + offset + row_index
                    row.extend([base, base + 1, base - 1, base + 0.5, 1000 + offset])
                values.append(row)
            return pd.DataFrame(values, index=dates, columns=columns)

        with patch.object(scanner.yf, "download", fake_download), \
             patch.object(scanner.yf, "Ticker", side_effect=AssertionError("per-ticker history should not be used")):
            result = scanner.fetch_batch_stock_data(["AAA", "BBB"], period="1y")

        self.assertEqual(calls, [("AAA", "BBB")])
        self.assertEqual(set(result), {"AAA", "BBB"})
        self.assertEqual(result["AAA"].attrs.get("source"), "yahoo")
        self.assertFalse(result["BBB"].empty)
        self.assertTrue(scanner.cache_path_for("AAA", "1y").exists())
        self.assertTrue(scanner.cache_path_for("BBB", "1y").exists())

    def test_fetch_common_market_data_downloads_market_specs_once(self):
        calls = []
        tickers = ["^TNX", "^VIX", "^VIX1D", "^SKEW"]

        def fake_download(tickers, period, group_by, auto_adjust, progress, threads):
            calls.append(tuple(tickers))
            dates = pd.date_range("2026-06-22", periods=2)
            columns = pd.MultiIndex.from_product([tickers, ["Close"]])
            values = [[10 + idx for idx, _ticker in enumerate(tickers)] for _ in range(2)]
            return pd.DataFrame(values, index=dates, columns=columns)

        with patch.object(scanner.yf, "download", fake_download), \
             patch.object(scanner, "fetch_history_with_retries", side_effect=AssertionError("per-market history should not be used")):
            result = scanner.fetch_common_market_data(period="1y")

        self.assertEqual(calls, [("^TNX", "^VIX", "^VIX1D", "^SKEW")])
        self.assertEqual(set(result), {"treasury", "vix", "vix1d", "skew"})
        self.assertEqual(result["vix"].loc[0, "VIX"], 11)


if __name__ == "__main__":
    unittest.main()
