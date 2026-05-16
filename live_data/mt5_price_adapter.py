
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from live_data.base_adapter import BaseMarketDataAdapter
from live_data.data_normalizer import DataNormalizer

class MT5PriceAdapter(BaseMarketDataAdapter):
    def __init__(self, source: str = "mt5"):
        self.source = source
        self._connected = False
        self._mt5 = None
        self._last_error = None
        self._try_import()

    def _try_import(self):
        try:
            import MetaTrader5 as mt5
            self._mt5 = mt5
        except ImportError:
            self._mt5 = None
            self._last_error = "MetaTrader5 package not installed"

    def connect(self) -> bool:
        if self._mt5 is None:
            self._last_error = "MT5 not available"
            return False
        try:
            result = self._mt5.initialize()
            self._connected = result
            return result
        except Exception as e:
            self._last_error = str(e)
            self._connected = False
            return False

    def disconnect(self) -> bool:
        if self._mt5:
            try:
                self._mt5.shutdown()
            except Exception:
                pass
        self._connected = False
        return True

    def is_connected(self) -> bool:
        return self._connected

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self._connected or self._mt5 is None:
            return None
        try:
            tick = self._mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            raw = {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "bid": tick.bid,
                "ask": tick.ask,
                "volume": tick.volume
            }
            return DataNormalizer.normalize_tick(raw, self.source)
        except Exception as e:
            self._last_error = str(e)
            return None

    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int) -> List[Dict[str, Any]]:
        if not self._connected or self._mt5 is None:
            return []
        try:
            tf_map = {"1m": self._mt5.TIMEFRAME_M1, "5m": self._mt5.TIMEFRAME_M5,
                      "15m": self._mt5.TIMEFRAME_M15, "1h": self._mt5.TIMEFRAME_H1}
            tf = tf_map.get(timeframe, self._mt5.TIMEFRAME_M1)
            rates = self._mt5.copy_rates_from_pos(symbol, tf, 0, lookback)
            if rates is None:
                return []
            bars = []
            for r in rates:
                raw = {
                    "symbol": symbol,
                    "timestamp": datetime.fromtimestamp(r["time"], tz=timezone.utc).isoformat(),
                    "open": r["open"],
                    "high": r["high"],
                    "low": r["low"],
                    "close": r["close"],
                    "volume": r.get("tick_volume", r.get("volume", 0))
                }
                bar = DataNormalizer.normalize_bar(raw, self.source)
                if bar:
                    bars.append(bar)
            return bars
        except Exception as e:
            self._last_error = str(e)
            return []

    def health_check(self) -> Dict[str, Any]:
        return {
            "connected": self._connected,
            "mt5_available": self._mt5 is not None,
            "last_error": self._last_error
        }
