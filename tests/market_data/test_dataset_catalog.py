"""
Test dataset catalog scanning.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import tempfile
import csv
from market_data.dataset_catalog import scan_datasets, list_datasets_table


def test_scan_temp_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a sample CSV
        path = os.path.join(tmpdir, "mt5_EURUSD_H1.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "open", "high", "low", "close", "tick_volume"])
            writer.writerow(["2024.01.15 10:00", "1.1000", "1.1005", "1.0995", "1.1002", "1000"])
            writer.writerow(["2024.01.15 11:00", "1.1002", "1.1008", "1.1000", "1.1005", "1200"])

        datasets = scan_datasets(tmpdir)
        assert len(datasets) == 1
        assert datasets[0]["symbol"] == "EURUSD"
        assert datasets[0]["timeframe"] == "H1"
        assert datasets[0]["source"] == "mt5"
        assert datasets[0]["row_count"] == 2


def test_list_datasets_table():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "GBPUSD_M5.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "open", "high", "low", "close", "volume"])
            writer.writerow(["2024.01.15 10:00", "1.3000", "1.3005", "1.2995", "1.3002", "500"])
        table = list_datasets_table(tmpdir)
        assert "GBPUSD" in table
        assert "M5" in table
