from typing import List, Dict, Any, Callable, Optional
from backtesting.backtest_engine import BacktestEngine
from backtesting.data_feed import HistoricalDataFeed


class WalkForward:
    """Expanding-window walk-forward validation.

    Strategies may train on each fold's preceding data via either:
    - trainer(strategy, train_data), or
    - strategy.fit(train_data), or
    - strategy.train(train_data).

    If no training hook exists, the result explicitly reports
    training_applied=False rather than implying optimization occurred.
    """

    def __init__(
        self,
        data: List[Dict[str, Any]],
        strategy_factory,
        n_folds: int = 5,
        trainer: Optional[Callable[[Any, List[Dict[str, Any]]], Any]] = None,
    ):
        if n_folds <= 0:
            raise ValueError("n_folds must be positive")
        self.data = data
        self.strategy_factory = strategy_factory
        self.n_folds = n_folds
        self.trainer = trainer

    def _build_strategy(self, train_data: List[Dict[str, Any]]):
        strategy = self.strategy_factory()
        training_applied = False

        if train_data:
            if self.trainer is not None:
                trained = self.trainer(strategy, train_data)
                if trained is not None:
                    strategy = trained
                training_applied = True
            elif hasattr(strategy, "fit") and callable(strategy.fit):
                strategy.fit(train_data)
                training_applied = True
            elif hasattr(strategy, "train") and callable(strategy.train):
                strategy.train(train_data)
                training_applied = True

        return strategy, training_applied

    def run(self) -> List[Dict[str, Any]]:
        if not self.data:
            return []

        fold_size = max(1, len(self.data) // self.n_folds)
        results = []

        for i in range(self.n_folds):
            start = i * fold_size
            if start >= len(self.data):
                break
            end = start + fold_size if i < self.n_folds - 1 else len(self.data)

            train_data = self.data[:start]
            test_data = self.data[start:end]
            if not test_data:
                continue

            strategy, training_applied = self._build_strategy(train_data)
            feed = HistoricalDataFeed(test_data)
            engine = BacktestEngine(feed, strategy)
            result = engine.run()
            result["fold"] = i + 1
            result["train_size"] = len(train_data)
            result["test_size"] = len(test_data)
            result["training_applied"] = training_applied
            result["validation_mode"] = "expanding_window"
            results.append(result)

        return results
