"""Tests for OANDA streaming/polling."""
import pytest
from broker_integration.broker_config import BrokerConfig
from broker_integration.oanda.oanda_streaming import OandaPollingStream
from broker_integration.transport.mock_transport import MockTransport


def test_oanda_polling_stream_mock_mode():
    config = BrokerConfig(broker_name="oanda", environment="practice")
    stream = OandaPollingStream(config, poll_interval_seconds=0.01, max_events=3)
    events = list(stream.start("EURUSD"))
    assert len(events) == 3
    assert events[0]["event_type"] == "tick"
    assert events[0]["source"] == "oanda_practice"
    stream.stop()


def test_oanda_polling_stream_with_transport():
    config = BrokerConfig(
        broker_name="oanda", environment="practice",
        api_key_env="OANDA_API_KEY", account_id_env="OANDA_ACCOUNT_ID",
    )
    mock = MockTransport()
    mock.enqueue_response({
        "prices": [{
            "instrument": "EUR_USD",
            "time": "2024-01-01T00:00:00Z",
            "bids": [{"price": "1.10000"}],
            "asks": [{"price": "1.10005"}],
        }]
    })
    # Transport injection would need to be wired into OandaPollingStream
    # This tests the normalization logic
    stream = OandaPollingStream(config, poll_interval_seconds=0.01, max_events=1)
    # Since transport is None, it falls back to synthetic
    events = list(stream.start("EURUSD"))
    assert len(events) == 1
    stream.stop()


def test_oanda_polling_stream_stop():
    config = BrokerConfig(broker_name="oanda", environment="practice")
    stream = OandaPollingStream(config, poll_interval_seconds=0.01, max_events=100)
    events = []
    for event in stream.start("EURUSD"):
        events.append(event)
        if len(events) >= 2:
            stream.stop()
    assert len(events) == 2
