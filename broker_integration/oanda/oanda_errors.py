"""OANDA-specific errors."""
from broker_integration.transport.network_errors import TransportError


class OandaPracticeError(TransportError):
    pass


class OandaLiveEndpointError(OandaPracticeError):
    """Raised when a live endpoint is detected."""
    pass
