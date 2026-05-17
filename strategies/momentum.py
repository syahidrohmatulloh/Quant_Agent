"""
Cross-sectional momentum and relative strength strategy family.
Evidence-based institutional-style. Paper-only.
"""
from typing import Dict, Any, List
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult


class CrossSectionalMomentum(BaseStrategy):
    """Rank symbols by recent return; go long top N, short bottom N."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 20)
        top_n = self.config.params.get("top_n", 3)
        returns = []
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            start = bars[-(lookback + 1)]["close"]
            end = bars[-1]["close"]
            ret = (end - start) / start if start else 0.0
            returns.append((symbol, ret, bars[-1]["timestamp"]))
        if not returns:
            return StrategyResult(signals=[], metrics={"strategy": "cross_sectional_momentum"})
        returns.sort(key=lambda x: x[1], reverse=True)
        signals = []
        for i, (symbol, ret, ts) in enumerate(returns):
            if i < top_n:
                signals.append(StrategySignal(
                    timestamp=ts, symbol=symbol, signal="long",
                    weight=0.5, meta={"rank": i + 1, "return": round(ret, 6)}
                ))
            elif i >= len(returns) - top_n:
                signals.append(StrategySignal(
                    timestamp=ts, symbol=symbol, signal="short",
                    weight=-0.5, meta={"rank": i + 1, "return": round(ret, 6)}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=ts, symbol=symbol, signal="flat",
                    weight=0.0, meta={"rank": i + 1, "return": round(ret, 6)}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "cross_sectional_momentum"})


class RelativeStrength(BaseStrategy):
    """Rank symbols by RSI-like relative strength vs a baseline symbol."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 14)
        baseline = self.config.params.get("baseline", None)
        signals = []
        # Compute simple relative strength = recent return / baseline recent return
        baseline_ret = None
        if baseline and baseline in data:
            b_bars = data[baseline]
            if len(b_bars) >= lookback + 1:
                baseline_ret = (b_bars[-1]["close"] - b_bars[-(lookback + 1)]["close"]) / b_bars[-(lookback + 1)]["close"]
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            ret = (bars[-1]["close"] - bars[-(lookback + 1)]["close"]) / bars[-(lookback + 1)]["close"]
            rs = ret / baseline_ret if baseline_ret and baseline_ret != 0 else ret
            if rs > 0.02:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="long",
                    weight=min(rs, 1.0), meta={"rs": round(rs, 6)}
                ))
            elif rs < -0.02:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="short",
                    weight=max(rs, -1.0), meta={"rs": round(rs, 6)}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="flat",
                    weight=0.0, meta={"rs": round(rs, 6)}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "relative_strength"})
