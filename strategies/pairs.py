"""
Pairs trading signal generator.
Evidence-based institutional-style. Paper-only.
"""
from typing import Dict, Any, List
import math
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult


class PairsTradingSignal(BaseStrategy):
    """Generate signal based on spread z-score between two symbols."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        pair = self.config.params.get("pair", [])
        if len(pair) != 2:
            raise ValueError("pair must contain exactly two symbols")
        lookback = self.config.params.get("lookback", 20)
        threshold = self.config.params.get("threshold", 2.0)
        s1, s2 = pair
        if s1 not in data or s2 not in data:
            return StrategyResult(signals=[], metrics={"strategy": "pairs_trading", "error": "missing pair data"})
        b1, b2 = data[s1], data[s2]
        min_len = min(len(b1), len(b2))
        if min_len < lookback:
            return StrategyResult(signals=[], metrics={"strategy": "pairs_trading", "error": "insufficient data"})
        spreads = [b1[i]["close"] - b2[i]["close"] for i in range(-lookback, 0)]
        mean = sum(spreads) / len(spreads)
        variance = sum((s - mean) ** 2 for s in spreads) / len(spreads)
        std = math.sqrt(variance) if variance > 0 else 1e-9
        current_spread = b1[-1]["close"] - b2[-1]["close"]
        z = (current_spread - mean) / std
        signals = []
        ts = b1[-1]["timestamp"]
        if z > threshold:
            # spread too high: short s1, long s2
            signals.append(StrategySignal(timestamp=ts, symbol=s1, signal="short", weight=-0.5, meta={"z": round(z, 4), "pair": s2}))
            signals.append(StrategySignal(timestamp=ts, symbol=s2, signal="long", weight=0.5, meta={"z": round(z, 4), "pair": s1}))
        elif z < -threshold:
            signals.append(StrategySignal(timestamp=ts, symbol=s1, signal="long", weight=0.5, meta={"z": round(z, 4), "pair": s2}))
            signals.append(StrategySignal(timestamp=ts, symbol=s2, signal="short", weight=-0.5, meta={"z": round(z, 4), "pair": s1}))
        else:
            signals.append(StrategySignal(timestamp=ts, symbol=s1, signal="flat", weight=0.0, meta={"z": round(z, 4), "pair": s2}))
            signals.append(StrategySignal(timestamp=ts, symbol=s2, signal="flat", weight=0.0, meta={"z": round(z, 4), "pair": s1}))
        return StrategyResult(signals=signals, metrics={"strategy": "pairs_trading", "zscore": round(z, 4)})
