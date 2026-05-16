
import numpy as np
import pandas as pd
from typing import Optional

class VolatilityTargeting:
    def __init__(self, target_vol: float = 0.10, lookback: int = 30, max_leverage: float = 2.0):
        self.target_vol = target_vol
        self.lookback = lookback
        self.max_leverage = max_leverage

    def compute_scalar(self, returns: pd.Series) -> float:
        if len(returns) < self.lookback:
            return 1.0
        realized = returns.iloc[-self.lookback:].std() * np.sqrt(252)
        if realized <= 0 or np.isnan(realized):
            return 1.0
        scalar = self.target_vol / realized
        return min(scalar, self.max_leverage)

    def apply(self, weights: pd.Series, returns: pd.Series) -> pd.Series:
        scalar = self.compute_scalar(returns)
        return weights * scalar
