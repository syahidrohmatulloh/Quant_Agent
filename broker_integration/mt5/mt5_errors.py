"""
MT5 integration exception hierarchy.
"""


class MT5Error(Exception):
    """Base MT5 integration error."""
    pass


class MT5ModuleNotFoundError(MT5Error):
    """MetaTrader5 Python package is not installed."""
    pass


class MT5TerminalUnavailableError(MT5Error):
    """MT5 terminal is not running or not reachable."""
    pass


class MT5InitializationError(MT5Error):
    """Failed to initialize MT5 connection."""
    pass


class MT5SymbolError(MT5Error):
    """Symbol not found or not visible in Market Watch."""
    pass


class MT5DataError(MT5Error):
    """Failed to fetch market data from MT5."""
    pass


class MT5TimeframeError(MT5Error):
    """Unsupported or invalid timeframe."""
    pass
