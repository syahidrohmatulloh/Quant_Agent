"""Network and transport errors."""


class TransportError(Exception):
    """Base transport error."""
    pass


class NetworkTimeoutError(TransportError):
    pass


class RateLimitError(TransportError):
    pass


class UnauthorizedError(TransportError):
    pass


class ServerError(TransportError):
    pass


class LiveTradingDisabledError(Exception):
    """Raised when live trading is attempted on a paper-only system."""
    pass
