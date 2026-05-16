"""HTTP transport interface with retry, rate-limit, and auth."""
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from .network_errors import TransportError, NetworkTimeoutError, RateLimitError, UnauthorizedError, ServerError
from .retry_policy import RetryPolicy
from .rate_limit import RateLimiter
from .auth import EnvAuth
from .redaction import redact_headers, redact_url


def _reject_live_endpoint(base_url: str) -> None:
    lowered = str(base_url).lower()
    live_markers = ("api-fxtrade.oanda.com", "stream-fxtrade.oanda.com", "fxtrade.oanda.com")
    if any(marker in lowered for marker in live_markers):
        raise ValueError("Live endpoint rejected; only practice/paper endpoints are allowed")


def _phase9_reject_live_endpoint(base_url: str) -> None:
    lowered = str(base_url).lower()
    live_markers = (
        "api-fxtrade.oanda.com",
        "stream-fxtrade.oanda.com",
        "fxtrade.oanda.com",
        "api-live",
        "live",
    )
    # Allow practice/fxpractice even though the word "practice" is present.
    if "fxpractice" in lowered or "practice" in lowered or "paper" in lowered:
        return
    if any(marker in lowered for marker in live_markers):
        raise ValueError("Live endpoint rejected; only practice/paper endpoints are allowed")


class HttpTransport(ABC):
    """Abstract HTTP transport."""

    @abstractmethod
    def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def post(self, path: str, json_data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def stream(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None):
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class RequestsHttpTransport(HttpTransport):
    """Real HTTP transport using requests (optional dependency)."""

    def __init__(
        self,
        base_url: str,
        auth: EnvAuth,
        retry_policy: Optional[RetryPolicy] = None,
        rate_limiter: Optional[RateLimiter] = None,
        timeout_seconds: float = 10.0,
    ):
        _reject_live_endpoint(base_url)
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.retry_policy = retry_policy or RetryPolicy()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.timeout = timeout_seconds
        self._session = None

    def _get_session(self):
        if self._session is None:
            try:
                import requests
                self._session = requests.Session()
            except ImportError:
                raise TransportError("requests package not available")
        return self._session

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        self.rate_limiter.wait_if_needed()
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = kwargs.pop("headers", {})
        auth_headers = self.auth.build_headers()
        headers = {**auth_headers, **headers}

        last_exception = None
        for attempt in range(self.retry_policy.max_attempts):
            try:
                session = self._get_session()
                response = session.request(
                    method, url, headers=headers, timeout=self.timeout, **kwargs
                )
                if response.status_code == 429:
                    raise RateLimitError("Rate limited")
                if response.status_code == 401:
                    raise UnauthorizedError("Unauthorized")
                if response.status_code >= 500:
                    raise ServerError(f"Server error {response.status_code}")
                response.raise_for_status()
                return response.json() if response.text else {}
            except Exception as exc:
                last_exception = exc
                if attempt < self.retry_policy.max_attempts - 1:
                    if isinstance(exc, RateLimitError) and self.retry_policy.is_retryable_status(429):
                        self.retry_policy.sleep(attempt)
                        continue
                    if isinstance(exc, ServerError) and self.retry_policy.is_retryable_status(500):
                        self.retry_policy.sleep(attempt)
                        continue
                raise
        raise last_exception if last_exception else TransportError("Request failed")

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self._request("GET", path, params=params, headers=headers or {})

    def post(self, path: str, json_data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self._request("POST", path, json=json_data, headers=headers or {})

    def stream(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        auth_headers = self.auth.build_headers()
        headers = {**auth_headers, **(headers or {})}
        try:
            import requests
            response = requests.get(url, headers=headers, params=params, stream=True, timeout=self.timeout)
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            raise TransportError(f"Stream error: {exc}")

    def close(self) -> None:
        if self._session:
            self._session.close()
            self._session = None

    def __repr__(self) -> str:
        return f"RequestsHttpTransport(base_url={self.base_url}, auth=redacted)"

