"""Tests for market data stream abstraction."""
from streaming.market_data_stream import MarketDataStream


def test_market_data_stream_is_abstract():
    import inspect
    assert inspect.isabstract(MarketDataStream)
