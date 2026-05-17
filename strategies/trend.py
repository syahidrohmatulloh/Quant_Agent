"""
Trend-following / time-series momentum strategy family.
Evidence-based institutional-style. Paper-only.
"""
from typing import Dict, Any, List
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult
from datetime import datetime


class TimeSeriesMomentum(BaseStrategy):
    """Long if recent return > threshold, short if < -threshold."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 20)
        threshold = self.config.params.get("threshold", 0.01)
        signals = []
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            recent = bars[-lookback:]
            start_price = recent[0]["close"]
            end_price = recent[-1]["close"]
            ret = (end_price - start_price) / start_price if start_price else 0.0
            if ret > threshold:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"],
                    symbol=symbol,
                    signal="long",
                    weight=min(ret, 1.0),
                    meta={"lookback": lookback, "return": round(ret, 6)}
                ))
            elif ret < -threshold:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"],
                    symbol=symbol,
                    signal="short",
                    weight=max(ret, -1.0),
                    meta={"lookback": lookback, "return": round(ret, 6)}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"],
                    symbol=symbol,
                    signal="flat",
                    weight=0.0,
                    meta={"lookback": lookback, "return": round(ret, 6)}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "time_series_momentum"})


class MACrossover(BaseStrategy):
    """Moving average crossover: fast > slow -> long, fast < slow -> short."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        fast = self.config.params.get("fast", 5)
        slow = self.config.params.get("slow", 20)
        if fast >= slow:
            raise ValueError("fast period must be < slow period")
        signals = []
        for symbol, bars in data.items():
            if len(bars) < slow:
                continue
            closes = [b["close"] for b in bars]
            fast_ma = sum(closes[-fast:]) / fast
            slow_ma = sum(closes[-slow:]) / slow
            if fast_ma > slow_ma:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"],
                    symbol=symbol,
                    signal="long",
                    weight=0.5,
                    meta={"fast_ma": round(fast_ma, 6), "slow_ma": round(slow_ma, 6)}
                ))
            elif fast_ma < slow_ma:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"],
                    symbol=symbol,
                    signal="short",
                    weight=-0.5,
                    meta={"fast_ma": round(fast_ma, 6), "slow_ma": round(slow_ma, 6)}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"],
                    symbol=symbol,
                    signal="flat",
                    weight=0.0,
                    meta={"fast_ma": round(fast_ma, 6), "slow_ma": round(slow_ma, 6)}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "ma_crossover"})


class ChannelBreakout(BaseStrategy):
    """Buy if price breaks highest high of lookback, sell if breaks lowest low."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 20)
        signals = []
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            window = bars[-(lookback + 1):-1]
            high = max(b["high"] for b in window)
            low = min(b["low"] for b in window)
            current = bars[-1]
            if current["close"] >= high:
                signals.append(StrategySignal(
                    timestamp=current["timestamp"],
                    symbol=symbol,
                    signal="long",
                    weight=0.5,
                    meta={"channel_high": high, "channel_low": low}
                ))
            elif current["close"] <= low:
                signals.append(StrategySignal(
                    timestamp=current["timestamp"],
                    symbol=symbol,
                    signal="short",
                    weight=-0.5,
                    meta={"channel_high": high, "channel_low": low}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=current["timestamp"],
                    symbol=symbol,
                    signal="flat",
                    weight=0.0,
                    meta={"channel_high": high, "channel_low": low}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "channel_breakout"})
