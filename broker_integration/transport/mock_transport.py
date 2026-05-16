
class _MockResponse:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload if payload is not None else {}
        self.status_code = status_code
        self.text = str(self._payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


"""Mock HTTP transport for testing — deterministic, no network."""
import json
from typing import Dict, Any, Optional, List, Callable
from collections import deque

from .http_transport import HttpTransport
from .network_errors import TransportError, NetworkTimeoutError, RateLimitError, UnauthorizedError, ServerError


class MockTransport(HttpTransport):
    """Mock HTTP transport with response queue and error simulation."""

    def __init__(self):
        self._responses: deque = deque()
        self._errors: deque = deque()
        self._requests: List[Dict[str, Any]] = []
        self._default_response: Optional[Dict[str, Any]] = None

    def enqueue_response(self, response: Dict[str, Any]) -> None:
        self._responses.append(response)

    def enqueue_error(self, error: Exception) -> None:
        self._errors.append(error)

    def set_default_response(self, response: Dict[str, Any]) -> None:
        self._default_response = response

    def _next(self):
        if self._errors:
            raise self._errors.popleft()
        if self._responses:
            return self._responses.popleft()
        if self._default_response is not None:
            return self._default_response
        return {}

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        self._requests.append({"method": "GET", "path": path, "params": params, "headers": headers})
        return self._next()

    def post(self, path: str, json_data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        self._requests.append({"method": "POST", "path": path, "json": json_data, "headers": headers})
        return self._next()

    def stream(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None):
        self._requests.append({"method": "STREAM", "path": path, "params": params, "headers": headers})
        # Yield from queued responses for stream
        while self._responses:
            yield self._responses.popleft()

    def close(self) -> None:
        pass

    @property
    def requests(self) -> List[Dict[str, Any]]:
        return self._requests

    def clear(self) -> None:
        self._requests.clear()
        self._responses.clear()
        self._errors.clear()

    def request(self, method, url, headers=None, timeout=None, **kwargs):
        method = str(method).upper()
        if method == "GET":
            payload = self.get(url, params=kwargs.get("params"), headers=headers)
        elif method == "POST":
            payload = self.post(url, json=kwargs.get("json"), headers=headers)
        else:
            payload = self.default_response if hasattr(self, "default_response") else {}
        return _MockResponse(payload, 200)
