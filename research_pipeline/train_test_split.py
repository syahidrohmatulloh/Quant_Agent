
import pandas as pd
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass

@dataclass
class SplitResult:
    train: pd.DataFrame
    test: pd.DataFrame
    train_indices: List[int]
    test_indices: List[int]
    purge_indices: List[int]
    method: str

class TimeSeriesSplit:
    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits

    def split(self, df: pd.DataFrame) -> List[SplitResult]:
        n = len(df)
        fold_size = n // self.n_splits
        results = []
        for i in range(self.n_splits):
            test_start = i * fold_size
            test_end = test_start + fold_size if i < self.n_splits - 1 else n
            train = df.iloc[:test_start]
            test = df.iloc[test_start:test_end]
            results.append(SplitResult(
                train=train, test=test,
                train_indices=list(train.index),
                test_indices=list(test.index),
                purge_indices=[],
                method="time_series"
            ))
        return results

class PurgedSplit:
    def __init__(self, embargo_pct: float = 0.01):
        self.embargo_pct = embargo_pct

    def split(self, df: pd.DataFrame, train_pct: float = 0.8) -> SplitResult:
        n = len(df)
        train_end = int(n * train_pct)
        embargo = int(n * self.embargo_pct)
        train = df.iloc[:train_end]
        purge = df.iloc[train_end:train_end + embargo]
        test = df.iloc[train_end + embargo:]
        return SplitResult(
            train=train, test=test,
            train_indices=list(train.index),
            test_indices=list(test.index),
            purge_indices=list(purge.index),
            method="purged"
        )

class WalkForwardSplit:
    def __init__(self, train_size: int, test_size: int, step_size: int):
        self.train_size = train_size
        self.test_size = test_size
        self.step_size = step_size

    def split(self, df: pd.DataFrame) -> List[SplitResult]:
        n = len(df)
        results = []
        start = 0
        while start + self.train_size + self.test_size <= n:
            train = df.iloc[start:start + self.train_size]
            test = df.iloc[start + self.train_size:start + self.train_size + self.test_size]
            results.append(SplitResult(
                train=train, test=test,
                train_indices=list(train.index),
                test_indices=list(test.index),
                purge_indices=[],
                method="walk_forward"
            ))
            start += self.step_size
        return results
