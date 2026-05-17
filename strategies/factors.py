"""
Multi-factor ranking: quality / value / momentum / defensive scoring.
Evidence-based institutional-style. Paper-only.
"""
from typing import Dict, Any, List
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult


class MultiFactorRanking(BaseStrategy):
    """
    Composite score from momentum, volatility, and mean-reversion factors.
    Long top N, short bottom N based on composite z-score.
    """

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        lookback = self.config.params.get("lookback", 20)
        top_n = self.config.params.get("top_n", 3)
        scores = []
        for symbol, bars in data.items():
            if len(bars) < lookback + 1:
                continue
            # Momentum factor: recent return
            mom = (bars[-1]["close"] - bars[-(lookback + 1)]["close"]) / bars[-(lookback + 1)]["close"]
            # Volatility factor: inverse of realized vol (defensive)
            returns = []
            for i in range(-lookback, 0):
                ret = (bars[i]["close"] - bars[i - 1]["close"]) / bars[i - 1]["close"]
                returns.append(ret)
            mean_ret = sum(returns) / len(returns)
            var = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
            vol = var ** 0.5 if var > 0 else 1e-9
            defensive = -vol  # lower vol is better
            # Mean reversion factor: z-score
            closes = [b["close"] for b in bars[-lookback:]]
            mean_c = sum(closes) / len(closes)
            std_c = (sum((c - mean_c) ** 2 for c in closes) / len(closes)) ** 0.5
            z = (closes[-1] - mean_c) / std_c if std_c > 0 else 0
            # Composite: momentum + defensive - mean_reversion (trend-following bias)
            composite = mom + defensive * 10 - z * 0.1
            scores.append((symbol, composite, bars[-1]["timestamp"]))
        if not scores:
            return StrategyResult(signals=[], metrics={"strategy": "multi_factor_ranking"})
        scores.sort(key=lambda x: x[1], reverse=True)
        signals = []
        for i, (symbol, score, ts) in enumerate(scores):
            if i < top_n:
                signals.append(StrategySignal(
                    timestamp=ts, symbol=symbol, signal="long",
                    weight=0.5, meta={"composite": round(score, 6), "rank": i + 1}
                ))
            elif i >= len(scores) - top_n:
                signals.append(StrategySignal(
                    timestamp=ts, symbol=symbol, signal="short",
                    weight=-0.5, meta={"composite": round(score, 6), "rank": i + 1}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=ts, symbol=symbol, signal="flat",
                    weight=0.0, meta={"composite": round(score, 6), "rank": i + 1}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "multi_factor_ranking"})
