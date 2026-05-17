import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from broker_integration.mt5.mt5_market_data import MT5MarketData
from broker_integration.mt5.mt5_errors import MT5ModuleNotFoundError, MT5InitializationError, MT5SymbolError, MT5DataError


class FakeTick:
    time = 1700000000
    bid = 1.1001
    ask = 1.1003
    last = 1.1002
    volume = 100
    time_msc = 1700000000123
    flags = 1


class FakeSymbol:
    name = "EURUSD"


def _make_fake_mt5():
    mt5 = MagicMock()
    mt5.initialize.return_value = True
    mt5.last_error.return_value = (0, "OK")
    mt5.symbols_get.return_value = [FakeSymbol()]
    mt5.symbol_info_tick.return_value = FakeTick()
    mt5.copy_rates_from_pos.return_value = [
        (1700000000, 1.1000, 1.1005, 1.0995, 1.1002, 1000, 2, 5000),
        (1700003600, 1.1002, 1.1008, 1.1000, 1.1005, 1200, 2, 6000),
    ]
    mt5.copy_rates_range.return_value = [
        (1700000000, 1.1000, 1.1005, 1.0995, 1.1002, 1000, 2, 5000),
    ]
    mt5.shutdown.return_value = None
    return mt5


def test_import_mt5_missing():
    with patch.dict("sys.modules", {"MetaTrader5": None}):
        with pytest.raises(MT5ModuleNotFoundError):
            MT5MarketData().initialize()


def test_initialize_success():
    fake = _make_fake_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": fake}):
        client = MT5MarketData(config={"timeout": 5000})
        assert client.initialize() is True
        assert client.is_initialized()
        client.shutdown()
        assert not client.is_initialized()


def test_initialize_failure():
    fake = _make_fake_mt5()
    fake.initialize.return_value = False
    fake.last_error.return_value = (-1, "Terminal not found")
    with patch.dict("sys.modules", {"MetaTrader5": fake}):
        client = MT5MarketData()
        with pytest.raises(MT5InitializationError):
            client.initialize()


def test_get_visible_symbols():
    fake = _make_fake_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": fake}):
        client = MT5MarketData()
        client.initialize()
        symbols = client.get_visible_symbols()
        assert "EURUSD" in symbols
        client.shutdown()


def test_symbol_info_tick():
    fake = _make_fake_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": fake}):
        client = MT5MarketData()
        client.initialize()
        tick = client.symbol_info_tick("EURUSD")
        assert tick["symbol"] == "EURUSD"
        assert tick["bid"] == 1.1001
        assert tick["ask"] == 1.1003
        assert tick["source"] == "mt5"
        assert isinstance(tick["timestamp"], datetime)
        client.shutdown()


def test_symbol_info_tick_missing():
    fake = _make_fake_mt5()
    fake.symbol_info_tick.return_value = None
    with patch.dict("sys.modules", {"MetaTrader5": fake}):
        client = MT5MarketData()
        client.initialize()
        with pytest.raises(MT5SymbolError):
            client.symbol_info_tick("MISSING")
        client.shutdown()


def test_copy_rates_from_pos():
    fake = _make_fake_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": fake}):
        client = MT5MarketData()
        client.initialize()
        bars = client.copy_rates_from_pos("EURUSD", "H1", count=2)
        assert len(bars) == 2
        assert bars[0]["symbol"] == "EURUSD"
        assert bars[0]["timeframe"] == "H1"
        assert bars[0]["source"] == "mt5"
        assert bars[0]["open"] == 1.1000
        assert bars[0]["high"] == 1.1005
        assert bars[0]["low"] == 1.0995
        assert bars[0]["close"] == 1.1002
        assert bars[0]["tick_volume"] == 1000
        assert bars[0]["spread"] == 2
        assert bars[0]["real_volume"] == 5000
        client.shutdown()


def test_copy_rates_range():
    fake = _make_fake_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": fake}):
        client = MT5MarketData()
        client.initialize()
        df = datetime(2023, 11, 14)
        dt = datetime(2023, 11, 15)
        bars = client.copy_rates_range("EURUSD", "H1", df, dt)
        assert len(bars) == 1
        assert bars[0]["symbol"] == "EURUSD"
        client.shutdown()


def test_context_manager():
    fake = _make_fake_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": fake}):
        with MT5MarketData() as client:
            assert client.is_initialized()
            tick = client.symbol_info_tick("EURUSD")
            assert tick["bid"] == 1.1001


def test_require_initialized():
    client = MT5MarketData()
    from broker_integration.mt5.mt5_errors import MT5TerminalUnavailableError
    with pytest.raises(MT5TerminalUnavailableError):
        client.symbol_info_tick("EURUSD")
