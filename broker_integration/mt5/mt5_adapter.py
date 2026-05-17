"""
MT5 adapter for Phase 10 strategy library.
Converts MT5 OHLCV data into the Dict[str, List[Dict]] shape expected by strategies.
Data-only. No order execution.
"""
from typing import List, Dict, Any
from broker_integration.mt5.mt5_market_data import MT5MarketData


class MT5StrategyAdapter:
    """
    Adapter that fetches MT5 data and feeds it into Phase 10 strategies.
    Paper-only. No live trading.
    """

    def __init__(self, market_data: MT5MarketData):
        self.market_data = market_data

    def fetch_for_strategy(
        self,
        symbols: List[str],
        timeframe: str = "H1",
        count: int = 100,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch MT5 OHLCV and return in strategy-compatible shape.
        Returns: {symbol: [bar_dict, ...]}
        """
        data: Dict[str, List[Dict[str, Any]]] = {}
        for sym in symbols:
            bars = self.market_data.copy_rates_from_pos(sym, timeframe, count)
            # Strip extra fields to keep strategy input clean
            clean = []
            for b in bars:
                clean.append({
                    "timestamp": b["timestamp"],
                    "open": b["open"],
                    "high": b["high"],
                    "low": b["low"],
                    "close": b["close"],
                    "volume": b["tick_volume"],
                })
            data[sym] = clean
        return data
