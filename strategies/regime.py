"""
Regime filters: volatility regime, trend regime, risk-on/risk-off.
Evidence-based institutional-style. Paper-only.
"""
from typing import Dict, Any, List
import math
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult


class VolatilityRegime(BaseStrategy):
    """Classify market into low / normal / high vol regime."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 20)
        high_threshold = self.config.params.get("high_threshold", 0.02)
        signals = []
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            returns = []
            for i in range(-lookback, 0):
                ret = (bars[i]["close"] - bars[i - 1]["close"]) / bars[i - 1]["close"]
                returns.append(ret)
            vol = math.sqrt(sum((r - sum(returns) / len(returns)) ** 2 for r in returns) / len(returns))
            if vol > high_threshold:
                regime = "high_vol"
                sig = "flat"  # de-risk in high vol
                weight = 0.0
            elif vol < high_threshold * 0.5:
                regime = "low_vol"
                sig = "long"
                weight = 0.3
            else:
                regime = "normal"
                sig = "long"
                weight = 0.5
            signals.append(StrategySignal(
                timestamp=bars[-1]["timestamp"], symbol=symbol, signal=sig,
                weight=weight, meta={"regime": regime, "vol": round(vol, 6)}
            ))
        return StrategyResult(signals=signals, metrics={"strategy": "volatility_regime"})


class TrendRegime(BaseStrategy):
    """Classify market into trending / ranging using ADX-like proxy."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 20)
        signals = []
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            dm_plus = []
            dm_minus = []
            for i in range(-lookback, 0):
                up = bars[i]["high"] - bars[i - 1]["high"]
                down = bars[i - 1]["low"] - bars[i]["low"]
                dm_plus.append(max(up, 0) if up > down else 0)
                dm_minus.append(max(down, 0) if down > up else 0)
            avg_dm_plus = sum(dm_plus) / len(dm_plus)
            avg_dm_minus = sum(dm_minus) / len(dm_minus)
            # Simple proxy: if DM+ > DM- -> uptrend, else ranging/downtrend
            if avg_dm_plus > avg_dm_minus * 1.2:
                regime = "uptrend"
                sig = "long"
                weight = 0.5
            elif avg_dm_minus > avg_dm_plus * 1.2:
                regime = "downtrend"
                sig = "short"
                weight = -0.5
            else:
                regime = "ranging"
                sig = "flat"
                weight = 0.0
            signals.append(StrategySignal(
                timestamp=bars[-1]["timestamp"], symbol=symbol, signal=sig,
                weight=weight, meta={"regime": regime, "dm_plus": round(avg_dm_plus, 6), "dm_minus": round(avg_dm_minus, 6)}
            ))
        return StrategyResult(signals=signals, metrics={"strategy": "trend_regime"})


class RiskOnOffFilter(BaseStrategy):
    """Simple risk-on/risk-off using a proxy safe-haven symbol."""

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        safe_haven = self.config.params.get("safe_haven", "USDJPY")
        lookback = self.config.params.get("lookback", 10)
        signals = []
        if safe_haven in data and len(data[safe_haven]) >= lookback + 1:
            b = data[safe_haven]
            ret = (b[-1]["close"] - b[-(lookback + 1)]["close"]) / b[-(lookback + 1)]["close"]
            if ret > 0.005:
                regime = "risk_off"
                default_sig = "flat"
            elif ret < -0.005:
                regime = "risk_on"
                default_sig = "long"
            else:
                regime = "neutral"
                default_sig = "flat"
        else:
            regime = "unknown"
            default_sig = "flat"
        for symbol, bars in data.items():
            signals.append(StrategySignal(
                timestamp=bars[-1]["timestamp"], symbol=symbol, signal=default_sig,
                weight=0.0 if default_sig == "flat" else 0.3,
                meta={"regime": regime, "safe_haven": safe_haven}
            ))
        return StrategyResult(signals=signals, metrics={"strategy": "risk_on_off"})
