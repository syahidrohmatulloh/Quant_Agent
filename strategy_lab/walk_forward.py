"""
Deterministic walk-forward validation helper.
Paper-only. No profitability guarantees.
"""
from typing import Dict, Any, List
from strategies.base import BaseStrategy, StrategyConfig
from strategy_lab.backtest import SimpleBacktestEngine


class WalkForwardValidation:
    def __init__(self, data: Dict[str, List[Dict[str, Any]]], strategy_factory,
                 train_frac: float = 0.6, test_frac: float = 0.2,
                 n_folds: int = 3):
        self.data = data
        self.strategy_factory = strategy_factory
        self.train_frac = train_frac
        self.test_frac = test_frac
        self.n_folds = n_folds

    def run(self) -> List[Dict[str, Any]]:
        min_bars = min(len(v) for v in self.data.values()) if self.data else 0
        if min_bars < 10:
            return []
        fold_size = max(1, int(min_bars / self.n_folds))
        results = []
        for i in range(self.n_folds):
            start = i * fold_size
            end = start + fold_size if i < self.n_folds - 1 else min_bars
            train_end = start + int(fold_size * self.train_frac)
            test_end = min(end, train_end + int(fold_size * self.test_frac))
            if test_end <= train_end:
                continue
            train_data = {sym: bars[start:train_end] for sym, bars in self.data.items()}
            test_data = {sym: bars[train_end:test_end] for sym, bars in self.data.items()}
            if not any(test_data.values()):
                continue
            strategy = self.strategy_factory()
            engine = SimpleBacktestEngine(test_data, strategy)
            result = engine.run()
            result["fold"] = i + 1
            result["train_size"] = train_end - start
            result["test_size"] = test_end - train_end
            results.append(result)
        return results
