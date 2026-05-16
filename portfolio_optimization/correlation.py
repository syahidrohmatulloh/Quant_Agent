
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

class CorrelationAnalyzer:
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold

    def compute(self, returns: pd.DataFrame) -> pd.DataFrame:
        return returns.corr()

    def high_correlation_pairs(self, corr: pd.DataFrame) -> List[Tuple[str, str, float]]:
        pairs = []
        cols = corr.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr.iloc[i, j]
                if abs(val) >= self.threshold:
                    pairs.append((cols[i], cols[j], round(float(val), 4)))
        return pairs

    def cluster_warning(self, corr: pd.DataFrame) -> Dict[str, List[str]]:
        # Simple clustering: groups of symbols with avg corr > threshold
        groups: Dict[str, List[str]] = {}
        cols = list(corr.columns)
        visited = set()
        for c in cols:
            if c in visited:
                continue
            group = [c]
            visited.add(c)
            for other in cols:
                if other not in visited and abs(corr.loc[c, other]) >= self.threshold:
                    group.append(other)
                    visited.add(other)
            if len(group) > 1:
                groups[c] = group
        return groups
