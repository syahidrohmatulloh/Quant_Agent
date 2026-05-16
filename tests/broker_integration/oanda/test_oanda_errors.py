"""Tests for OANDA error classes."""
from broker_integration.oanda.oanda_errors import OandaPracticeError, OandaLiveEndpointError


def test_oanda_error_is_transport():
    err = OandaPracticeError("test")
    assert str(err) == "test"


def test_live_endpoint_error():
    err = OandaLiveEndpointError("live url")
    assert "live url" in str(err)
