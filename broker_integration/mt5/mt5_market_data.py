"""
MetaTrader 5 market data ingestion.
Data-only. No order execution. No live trading.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from broker_integration.mt5.mt5_config import get_mt5_timeframe, get_string_timeframe
from broker_integration.mt5.mt5_errors import (
    MT5ModuleNotFoundError,
    MT5TerminalUnavailableError,
    MT5InitializationError,
    MT5SymbolError,
    MT5DataError,
    MT5TimeframeError,
)

logger = logging.getLogger(__name__)


def _import_mt5() -> Any:
    """Import MetaTrader5 module safely."""
    try:
        import MetaTrader5 as mt5
        return mt5
    except ImportError:
        raise MT5ModuleNotFoundError(
            "MetaTrader5 Python package is not installed. "
            "Install it via: pip install MetaTrader5"
        )


class MT5MarketData:
    """
    MT5 market data client. Data-only. No order submission.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._mt5 = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize MT5 terminal connection."""
        self._mt5 = _import_mt5()
        timeout = self.config.get("timeout", 60000)
        portable = self.config.get("portable", False)
        logger.info("Initializing MT5 connection (timeout=%s, portable=%s)", timeout, portable)
        ok = self._mt5.initialize(timeout=timeout, portable=portable)
        if not ok:
            err = self._mt5.last_error()
            raise MT5InitializationError(f"MT5 initialization failed: {err}")
        self._initialized = True
        logger.info("MT5 initialized successfully")
        return True

    def shutdown(self) -> None:
        """Safely shutdown MT5 connection."""
        if self._mt5 and self._initialized:
            self._mt5.shutdown()
            self._initialized = False
            logger.info("MT5 shutdown complete")

    def is_initialized(self) -> bool:
        return self._initialized

    def get_visible_symbols(self) -> List[str]:
        """Return list of symbols visible in Market Watch."""
        self._require_initialized()
        symbols = self._mt5.symbols_get()
        if symbols is None:
            raise MT5DataError("Failed to retrieve symbols from MT5")
        return [s.name for s in symbols]

    def symbol_info_tick(self, symbol: str) -> Dict[str, Any]:
        """Fetch latest tick for a symbol."""
        self._require_initialized()
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5SymbolError(f"Symbol {symbol} not found or no tick data")
        return {
            "symbol": symbol,
            "timestamp": datetime.fromtimestamp(tick.time),
            "bid": tick.bid,
            "ask": tick.ask,
            "last": tick.last,
            "volume": tick.volume,
            "time_msc": tick.time_msc,
            "flags": tick.flags,
            "source": "mt5",
        }

    def copy_rates_from_pos(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch historical OHLCV bars from current position backwards."""
        self._require_initialized()
        tf_int = get_mt5_timeframe(timeframe)
        rates = self._mt5.copy_rates_from_pos(symbol, tf_int, 0, count)
        if rates is None:
            raise MT5DataError(f"Failed to copy rates for {symbol} {timeframe}")
        return self._normalize_rates(rates, symbol, timeframe)

    def copy_rates_range(
        self, symbol: str, timeframe: str, date_from: datetime, date_to: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch historical OHLCV bars for a date range."""
        self._require_initialized()
        tf_int = get_mt5_timeframe(timeframe)
        rates = self._mt5.copy_rates_range(symbol, tf_int, date_from, date_to)
        if rates is None:
            raise MT5DataError(
                f"Failed to copy rates for {symbol} {timeframe} from {date_from} to {date_to}"
            )
        return self._normalize_rates(rates, symbol, timeframe)

    def _normalize_rates(
        self, rates: Any, symbol: str, timeframe: str
    ) -> List[Dict[str, Any]]:
        """Normalize MT5 rates array into Quant_Agent internal shape."""
        result = []
        for r in rates:
            ts = datetime.fromtimestamp(r[0])
            result.append({
                "timestamp": ts,
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "tick_volume": int(r[5]),
                "spread": int(r[6]) if len(r) > 6 else 0,
                "real_volume": int(r[7]) if len(r) > 7 else 0,
                "symbol": symbol,
                "timeframe": timeframe,
                "source": "mt5",
            })
        return result

    def _require_initialized(self) -> None:
        if not self._initialized:
            raise MT5TerminalUnavailableError("MT5 not initialized. Call initialize() first.")

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False
