"""
Volatility breakout / ATR breakout strategy family.
Evidence-based institutional-style. Paper-only.
"""
from typing import Dict, Any, List
import math
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult


class ATRBreakout(BaseStrategy):
    """Enter when close breaks previous close +/- k*ATR."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 14)
        multiplier = self.config.params.get("multiplier", 1.5)
        signals = []
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            trs = []
            for i in range(-lookback, 0):
                b = bars[i]
                prev = bars[i - 1]
                tr = max(b["high"] - b["low"], abs(b["high"] - prev["close"]), abs(b["low"] - prev["close"]))
                trs.append(tr)
            atr = sum(trs) / len(trs)
            prev_close = bars[-2]["close"]
            current = bars[-1]["close"]
            upper = prev_close + multiplier * atr
            lower = prev_close - multiplier * atr
            if current >= upper:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="long",
                    weight=0.5, meta={"atr": round(atr, 6), "upper": round(upper, 6)}
                ))
            elif current <= lower:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="short",
                    weight=-0.5, meta={"atr": round(atr, 6), "lower": round(lower, 6)}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="flat",
                    weight=0.0, meta={"atr": round(atr, 6)}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "atr_breakout"})


class VolatilityBreakout(BaseStrategy):
    """Enter when realized vol exceeds threshold (Bollinger-style)."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 20)
        threshold = self.config.params.get("threshold", 0.02)
        signals = []
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            returns = []
            for i in range(-lookback, 0):
                ret = (bars[i]["close"] - bars[i - 1]["close"]) / bars[i - 1]["close"]
                returns.append(ret)
            mean = sum(returns) / len(returns)
            vol = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns))
            current_ret = (bars[-1]["close"] - bars[-2]["close"]) / bars[-2]["close"]
            if abs(current_ret) > vol * threshold * 100:
                direction = "long" if current_ret > 0 else "short"
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal=direction,
                    weight=0.5, meta={"realized_vol": round(vol, 6), "current_ret": round(current_ret, 6)}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="flat",
                    weight=0.0, meta={"realized_vol": round(vol, 6)}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "volatility_breakout"})
