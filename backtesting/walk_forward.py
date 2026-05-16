
from typing import List, Dict, Any
from backtesting.backtest_engine import BacktestEngine
from backtesting.data_feed import HistoricalDataFeed
from research.strategy_base import StrategyBase

class WalkForward:
    def __init__(self, data: List[Dict[str, Any]], strategy_factory, n_folds: int = 5):
        self.data = data
        self.strategy_factory = strategy_factory
        self.n_folds = n_folds

    def run(self) -> List[Dict[str, Any]]:
        fold_size = len(self.data) // self.n_folds
        results = []
        for i in range(self.n_folds):
            start = i * fold_size
            end = start + fold_size if i < self.n_folds - 1 else len(self.data)
            train_data = self.data[:start] if start > 0 else []
            test_data = self.data[start:end]
            if not test_data:
                continue
            feed = HistoricalDataFeed(test_data)
            strategy = self.strategy_factory()
            engine = BacktestEngine(feed, strategy)
            result = engine.run()
            result["fold"] = i + 1
            result["train_size"] = len(train_data)
            result["test_size"] = len(test_data)
            results.append(result)
        return results
