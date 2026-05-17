"""
FX carry / rate differential ranking signal.
Evidence-based institutional-style. Paper-only.
Uses synthetic/fake rates in tests; never calls live rate APIs.
"""
from typing import Dict, Any, List
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult


class FXCarrySignal(BaseStrategy):
    """
    Rank symbols by implied rate differential.
    In production this would use real central-bank rate data;
    here we accept a 'rates' dict in config.params for paper/synthetic use.
    """

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        rates = self.config.params.get("rates", {})
        if not rates:
            # fallback: assign random-ish but deterministic synthetic rates based on symbol name hash
            rates = {sym: (hash(sym) % 100) / 1000.0 for sym in self.config.symbols}
        sorted_rates = sorted(rates.items(), key=lambda x: x[1], reverse=True)
        signals = []
        n = len(sorted_rates)
        for i, (symbol, rate) in enumerate(sorted_rates):
            if i < max(1, n // 3):
                signals.append(StrategySignal(
                    timestamp=data.get(symbol, [{"timestamp": None}])[-1].get("timestamp"),
                    symbol=symbol, signal="long", weight=0.5,
                    meta={"rate": rate, "rank": i + 1}
                ))
            elif i >= n - max(1, n // 3):
                signals.append(StrategySignal(
                    timestamp=data.get(symbol, [{"timestamp": None}])[-1].get("timestamp"),
                    symbol=symbol, signal="short", weight=-0.5,
                    meta={"rate": rate, "rank": i + 1}
                ))
            else:
                signals.append(StrategySignal(
                    timestamp=data.get(symbol, [{"timestamp": None}])[-1].get("timestamp"),
                    symbol=symbol, signal="flat", weight=0.0,
                    meta={"rate": rate, "rank": i + 1}
                ))
        return StrategyResult(signals=signals, metrics={"strategy": "fx_carry", "synthetic": not bool(self.config.params.get("rates"))})
