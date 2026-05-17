"""
Mean reversion / z-score / RSI strategy family.
Evidence-based institutional-style. Paper-only.
"""
from typing import Dict, Any, List
import math
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult


class ZScoreMeanReversion(BaseStrategy):
    """Go long when z-score < -threshold, short when > +threshold."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 20)
        threshold = self.config.params.get("threshold", 2.0)
        signals = []
        for symbol, bars in data.items():
            if len(bars) < lookback:
                continue
            closes = [b["close"] for b in bars[-lookback:]]
            mean = sum(closes) / len(closes)
            variance = sum((c - mean) ** 2 for c in closes) / len(closes)
            std = math.sqrt(variance) if variance > 0 else 1e-9
            z = (closes[-1] - mean) / std
            if z < -threshold:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="long",
                    weight=min(abs(z) / threshold, 1.0),
                    meta={"zscore": round(z, 4), "mean": round(mean, 6), "std": round(std, 6)}
                ))
            elif z > threshold:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="short",
                    weight=-min(abs(z) / threshold, 1.0),
                    meta={"zscore": round(z, 4), "mean": round(mean, 6), "std": round(std, 6)}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="flat",
                    weight=0.0,
                    meta={"zscore": round(z, 4), "mean": round(mean, 6), "std": round(std, 6)}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "zscore_mean_reversion"})


class RSImeanReversion(BaseStrategy):
    """Simple RSI-like mean reversion using smoothed gains/losses."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 14)
        oversold = self.config.params.get("oversold", 30)
        overbought = self.config.params.get("overbought", 70)
        signals = []
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            gains = []
            losses = []
            for i in range(1, lookback + 1):
                diff = bars[-i]["close"] - bars[-(i + 1)]["close"]
                if diff > 0:
                    gains.append(diff)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(diff))
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100.0 - (100.0 / (1.0 + rs))
            if rsi < oversold:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="long",
                    weight=(oversold - rsi) / oversold,
                    meta={"rsi": round(rsi, 2)}
                ))
            elif rsi > overbought:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="short",
                    weight=-(rsi - overbought) / (100 - overbought),
                    meta={"rsi": round(rsi, 2)}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=bars[-1]["timestamp"], symbol=symbol, signal="flat",
                    weight=0.0, meta={"rsi": round(rsi, 2)}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "rsi_mean_reversion"})
