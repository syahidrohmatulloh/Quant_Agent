"""Tests for market data normalization across brokers."""
from broker_integration.oanda.oanda_market_data import normalize_oanda_tick
from broker_integration.alpaca.alpaca_market_data import normalize_alpaca_tick
from broker_integration.ibkr.ibkr_market_data import normalize_ibkr_tick


def test_all_normalizations_have_required_fields():
    oanda = normalize_oanda_tick("EURUSD", {"bid": 1.1, "ask": 1.1005})
    alpaca = normalize_alpaca_tick("AAPL", {"bid_price": 150, "ask_price": 150.01})
    ibkr = normalize_ibkr_tick("AAPL", {"bid": 150, "ask": 150.01})

    required = {"symbol", "timestamp_utc", "bid", "ask", "mid", "spread", "volume", "source"}
    for tick in [oanda, alpaca, ibkr]:
        assert required.issubset(set(tick.keys()))
        assert tick["source"] in {"oanda_practice", "alpaca_paper", "ibkr_paper"}
