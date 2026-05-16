
import pytest
from live_data.data_normalizer import DataNormalizer

def test_normalize_tick():
    raw = {"symbol": "EURUSD", "bid": 1.1000, "ask": 1.1002, "volume": 100}
    tick = DataNormalizer.normalize_tick(raw, "test")
    assert tick["symbol"] == "EURUSD"
    assert tick["bid"] == 1.1000
    assert tick["ask"] == 1.1002
    assert tick["mid"] == 1.1001
    assert tick["spread"] == 0.0002
    assert tick["source"] == "test"

def test_normalize_tick_missing_bid():
    raw = {"symbol": "EURUSD", "ask": 1.1002}
    tick = DataNormalizer.normalize_tick(raw)
    assert tick is None

def test_normalize_tick_negative_price():
    raw = {"symbol": "EURUSD", "bid": -1.0, "ask": 1.1002}
    tick = DataNormalizer.normalize_tick(raw)
    assert tick is None

def test_normalize_tick_ask_below_bid():
    raw = {"symbol": "EURUSD", "bid": 1.1002, "ask": 1.1000}
    tick = DataNormalizer.normalize_tick(raw)
    assert tick is None

def test_normalize_bar():
    raw = {"symbol": "EURUSD", "open": 1.1000, "high": 1.1005, "low": 1.0995, "close": 1.1002, "volume": 100}
    bar = DataNormalizer.normalize_bar(raw, "test")
    assert bar["open"] == 1.1000
    assert bar["high"] == 1.1005
    assert bar["source"] == "test"

def test_normalize_bar_invalid_ohlc():
    raw = {"symbol": "EURUSD", "open": 1.1000, "high": 1.0990, "low": 1.1005, "close": 1.1002}
    bar = DataNormalizer.normalize_bar(raw)
    assert bar is None
