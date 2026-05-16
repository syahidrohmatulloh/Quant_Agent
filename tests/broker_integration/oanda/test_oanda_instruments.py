"""Tests for OANDA instrument utilities."""
from broker_integration.oanda.oanda_instruments import to_oanda_symbol, from_oanda_symbol, is_valid_oanda_symbol


def test_to_oanda_symbol():
    assert to_oanda_symbol("EURUSD") == "EUR_USD"
    assert to_oanda_symbol("eurusd") == "EUR_USD"
    assert to_oanda_symbol("EUR_USD") == "EUR_USD"
    assert to_oanda_symbol("GBPUSD") == "GBP_USD"
    assert to_oanda_symbol("XAUUSD") == "XAU_USD"


def test_from_oanda_symbol():
    assert from_oanda_symbol("EUR_USD") == "EURUSD"
    assert from_oanda_symbol("GBP_USD") == "GBPUSD"


def test_is_valid_oanda_symbol():
    assert is_valid_oanda_symbol("EUR_USD") is True
    assert is_valid_oanda_symbol("EURUSD") is False
    assert is_valid_oanda_symbol("ABC_DEF_GHI") is False
