"""Tests for mock HTTP transport."""
import pytest
from broker_integration.transport.mock_transport import MockTransport
from broker_integration.transport.network_errors import TransportError


def test_mock_transport_get():
    mock = MockTransport()
    mock.enqueue_response({"status": "ok"})
    result = mock.get("/test")
    assert result["status"] == "ok"
    assert len(mock.requests) == 1
    assert mock.requests[0]["method"] == "GET"
    assert mock.requests[0]["path"] == "/test"


def test_mock_transport_post():
    mock = MockTransport()
    mock.enqueue_response({"id": "123"})
    result = mock.post("/orders", json_data={"symbol": "EURUSD"})
    assert result["id"] == "123"
    assert mock.requests[0]["json"]["symbol"] == "EURUSD"


def test_mock_transport_error():
    mock = MockTransport()
    mock.enqueue_error(TransportError("simulated"))
    with pytest.raises(TransportError):
        mock.get("/test")


def test_mock_transport_stream():
    mock = MockTransport()
    mock.enqueue_response({"tick": 1})
    mock.enqueue_response({"tick": 2})
    results = list(mock.stream("/stream"))
    assert len(results) == 2
    assert results[0]["tick"] == 1


def test_mock_transport_default_response():
    mock = MockTransport()
    mock.set_default_response({"default": True})
    r1 = mock.get("/a")
    r2 = mock.get("/b")
    assert r1["default"] is True
    assert r2["default"] is True


def test_mock_transport_clear():
    mock = MockTransport()
    mock.enqueue_response({"x": 1})
    mock.get("/test")
    mock.clear()
    assert len(mock.requests) == 0
