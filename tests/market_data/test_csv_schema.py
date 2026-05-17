"""
Test CSV schema alias detection and filename inference.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from market_data.csv_schema import (
    normalize_column_name, infer_from_filename,
    TIMESTAMP_ALIASES, REQUIRED_PRICE_COLUMNS, VOLUME_ALIASES
)


def test_timestamp_aliases_coverage():
    for alias in TIMESTAMP_ALIASES:
        assert normalize_column_name(alias) == "timestamp"


def test_required_columns_coverage():
    for col in REQUIRED_PRICE_COLUMNS:
        assert normalize_column_name(col) == col


def test_volume_aliases_coverage():
    assert normalize_column_name("volume") == "volume"
    assert normalize_column_name("tick_volume") == "tick_volume"
    assert normalize_column_name("tickvol") == "tick_volume"
    assert normalize_column_name("vol") == "volume"


def test_infer_mt5_filename():
    meta = infer_from_filename("mt5_EURUSD_H1.csv")
    assert meta.symbol == "EURUSD"
    assert meta.timeframe == "H1"
    assert meta.source == "mt5"


def test_infer_plain_filename():
    meta = infer_from_filename("GBPUSD_M5.csv")
    assert meta.symbol == "GBPUSD"
    assert meta.timeframe == "M5"
    assert meta.source == "csv"


def test_infer_oanda_filename():
    meta = infer_from_filename("oanda_EUR_USD_M15.csv")
    assert meta.symbol == "EURUSD"
    assert meta.timeframe == "M15"
    assert meta.source == "oanda"
