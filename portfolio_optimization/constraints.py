
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

class Constraints:
    def __init__(self,
                 max_weight: float = 0.25,
                 min_weight: float = 0.0,
                 max_gross_exposure: float = 1.5,
                 max_net_exposure: float = 1.0,
                 max_leverage: float = 2.0,
                 max_correlated_exposure: float = 0.5,
                 mode: str = "long_short"):
        self.max_weight = max_weight
        self.min_weight = min_weight
        self.max_gross_exposure = max_gross_exposure
        self.max_net_exposure = max_net_exposure
        self.max_leverage = max_leverage
        self.max_correlated_exposure = max_correlated_exposure
        self.mode = mode

    def apply(self, weights: pd.Series, high_corr_pairs: Optional[list] = None) -> pd.Series:
        w = weights.copy()
        # Clip individual weights
        w = w.clip(lower=self.min_weight, upper=self.max_weight)
        # Mode constraint
        if self.mode == "long_only":
            w = w.clip(lower=0.0)
        # Normalize gross exposure
        gross = w.abs().sum()
        if gross > self.max_gross_exposure:
            w = w * (self.max_gross_exposure / gross)
        # Net exposure cap
        net = w.sum()
        if abs(net) > self.max_net_exposure:
            w = w * (self.max_net_exposure / abs(net))
        # Leverage cap
        lev = w.abs().sum()
        if lev > self.max_leverage:
            w = w * (self.max_leverage / lev)
        # Correlated exposure cap (simple: reduce both in pair)
        if high_corr_pairs:
            for sym1, sym2, _ in high_corr_pairs:
                if sym1 in w.index and sym2 in w.index:
                    combined = abs(w[sym1]) + abs(w[sym2])
                    if combined > self.max_correlated_exposure:
                        factor = self.max_correlated_exposure / combined
                        w[sym1] *= factor
                        w[sym2] *= factor
        return w
