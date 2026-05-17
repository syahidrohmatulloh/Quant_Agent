import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import pytest
from unittest.mock import MagicMock, patch
from broker_integration.mt5.mt5_adapter import MT5StrategyAdapter
from broker_integration.mt5.mt5_market_data import MT5MarketData


class FakeTick:
    time = 1700000000
    bid = 1.1001
    ask = 1.1003
    last = 1.1002
    volume = 100
    time_msc = 1700000000123
    flags = 1


def _make_fake_mt5():
    mt5 = MagicMock()
    mt5.initialize.return_value = True
    mt5.last_error.return_value = (0, "OK")
    mt5.symbols_get.return_value = []
    mt5.symbol_info_tick.return_value = FakeTick()
    mt5.copy_rates_from_pos.return_value = [
        (1700000000, 1.1000, 1.1005, 1.0995, 1.1002, 1000, 2, 5000),
        (1700003600, 1.1002, 1.1008, 1.1000, 1.1005, 1200, 2, 6000),
    ]
    mt5.shutdown.return_value = None
    return mt5


def test_fetch_for_strategy():
    fake = _make_fake_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": fake}):
        client = MT5MarketData()
        client.initialize()
        adapter = MT5StrategyAdapter(client)
        data = adapter.fetch_for_strategy(["EURUSD"], "H1", count=2)
        assert "EURUSD" in data
        assert len(data["EURUSD"]) == 2
        bar = data["EURUSD"][0]
        assert set(bar.keys()) == {"timestamp", "open", "high", "low", "close", "volume"}
        assert bar["open"] == 1.1000
        assert bar["close"] == 1.1002
        assert bar["volume"] == 1000
        client.shutdown()
