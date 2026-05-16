
import pytest
from live_data.polling_adapter import PollingAdapter
from live_data.data_normalizer import DataNormalizer

def test_polling_returns_normalized_tick():
    def provider(symbol):
        return {"symbol": symbol, "bid": 1.1000, "ask": 1.1002, "volume": 100}
    adapter = PollingAdapter(provider, interval_seconds=1.0, max_retries=1)
    adapter.connect()
    tick = adapter.get_latest_tick("EURUSD")
    assert tick is not None
    assert tick["symbol"] == "EURUSD"
    assert tick["bid"] == 1.1000
    assert tick["ask"] == 1.1002
    adapter.disconnect()

def test_polling_retries_on_failure():
    call_count = [0]
    def provider(symbol):
        call_count[0] += 1
        if call_count[0] < 2:
            raise RuntimeError("fail")
        return {"symbol": symbol, "bid": 1.1, "ask": 1.1002}
    adapter = PollingAdapter(provider, interval_seconds=1.0, max_retries=3)
    adapter.connect()
    tick = adapter.get_latest_tick("EURUSD")
    assert tick is not None
    assert call_count[0] == 2
    adapter.disconnect()

def test_polling_returns_last_tick_on_failure():
    def provider(symbol):
        return {"symbol": symbol, "bid": 1.1, "ask": 1.1002}
    adapter = PollingAdapter(provider, max_retries=1)
    adapter.connect()
    tick1 = adapter.get_latest_tick("EURUSD")
    # Now make provider fail
    adapter.provider = lambda s: (_ for _ in ()).throw(RuntimeError("fail"))
    tick2 = adapter.get_latest_tick("EURUSD")
    assert tick2 == tick1
    adapter.disconnect()

def test_health_check():
    def provider(symbol):
        return {"symbol": symbol, "bid": 1.1, "ask": 1.1002}
    adapter = PollingAdapter(provider)
    adapter.connect()
    adapter.get_latest_tick("EURUSD")
    health = adapter.health_check()
    assert health["connected"] is True
    assert health["has_last_tick"] is True
    adapter.disconnect()
