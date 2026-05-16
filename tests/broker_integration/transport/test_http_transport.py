"""Tests for HTTP transport."""
import pytest
from broker_integration.transport.http_transport import RequestsHttpTransport
from broker_integration.transport.auth import EnvAuth
from broker_integration.transport.network_errors import TransportError, RateLimitError, UnauthorizedError


def test_http_transport_repr_no_secrets():
    auth = EnvAuth(api_key_env="TEST_KEY")
    transport = RequestsHttpTransport(
        base_url="https://api-fxpractice.oanda.com",
        auth=auth,
    )
    r = repr(transport)
    assert "api-fxpractice" in r
    assert "Bearer" not in r
    assert "secret" not in r.lower()


def test_http_transport_live_endpoint_rejected():
    auth = EnvAuth(api_key_env="TEST_KEY")
    with pytest.raises(Exception):
        RequestsHttpTransport(
            base_url="https://api-fxtrade.oanda.com",
            auth=auth,
        )
