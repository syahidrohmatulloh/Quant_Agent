"""
Ensemble strategy selector: combine multiple strategy signals.
Evidence-based institutional-style. Paper-only.
No profitability claims.
"""
from typing import Dict, Any, List
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult


class EnsembleSelector(BaseStrategy):
    """
    Combine signals from multiple sub-strategies via voting or weighted average.
    Config params:
      - strategies: list of strategy names
      - method: "vote" or "average"
      - weights: optional dict of strategy_name -> weight
    """

    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        from strategies.registry import StrategyRegistry  # local import to avoid circular dependency
        sub_names = self.config.params.get("strategies", [])
        method = self.config.params.get("method", "vote")
        weights = self.config.params.get("weights", {})
        if not sub_names:
            return StrategyResult(signals=[], metrics={"strategy": "ensemble_selector", "error": "no sub-strategies"})
        all_results = []
        for name in sub_names:
            try:
                cls = StrategyRegistry.get(name)
                cfg = StrategyConfig(name=name, symbols=self.config.symbols, params=self.config.params.get(name, {}))
                instance = cls(cfg)
                result = instance.generate(data)
                all_results.append((name, result))
            except Exception as e:
                all_results.append((name, StrategyResult(signals=[], metrics={"error": str(e)})))
        # Aggregate per symbol
        symbol_signals: Dict[str, List[StrategySignal]] = {}
        for name, result in all_results:
            for sig in result.signals:
                symbol_signals.setdefault(sig.symbol, []).append(sig)
        aggregated = []
        for symbol, sigs in symbol_signals.items():
            if method == "average":
                total_weight = sum(s.weight * weights.get(s.symbol, 1.0) for s in sigs)
                count = len(sigs)
                avg = total_weight / count if count else 0.0
                if avg > 0.1:
                    sig_str = "long"
                elif avg < -0.1:
                    sig_str = "short"
                else:
                    sig_str = "flat"
                aggregated.append(StrategySignal(
                    timestamp=sigs[0].timestamp, symbol=symbol, signal=sig_str,
                    weight=round(avg, 4), meta={"method": "average", "count": count}
                ))
            else:  # vote
                longs = sum(1 for s in sigs if s.signal in ("long", "buy"))
                shorts = sum(1 for s in sigs if s.signal in ("short", "sell"))
                flats = sum(1 for s in sigs if s.signal in ("flat", "hold"))
                if longs > shorts and longs > flats:
                    sig_str = "long"
                    w = 0.5
                elif shorts > longs and shorts > flats:
                    sig_str = "short"
                    w = -0.5
                else:
                    sig_str = "flat"
                    w = 0.0
                aggregated.append(StrategySignal(
                    timestamp=sigs[0].timestamp, symbol=symbol, signal=sig_str,
                    weight=w, meta={"method": "vote", "longs": longs, "shorts": shorts, "flats": flats}
                ))
        return StrategyResult(
            signals=aggregated,
            metrics={"strategy": "ensemble_selector", "method": method, "sub_strategies": sub_names}
        )
