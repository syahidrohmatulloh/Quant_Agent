
import numpy as np
import pandas as pd
from typing import Optional

class RiskParityAllocator:
    def __init__(self):
        pass

    def allocate(self, cov: pd.DataFrame) -> pd.Series:
        inv_vol = 1.0 / np.sqrt(np.diag(cov.values))
        inv_vol = np.where(np.isfinite(inv_vol), inv_vol, 0.0)
        weights = inv_vol / inv_vol.sum() if inv_vol.sum() > 0 else np.ones(len(inv_vol)) / len(inv_vol)
        return pd.Series(weights, index=cov.index)

    def equal_risk_contribution(self, cov: pd.DataFrame, max_iter: int = 100) -> pd.Series:
        n = len(cov)
        w = np.ones(n) / n
        for _ in range(max_iter):
            sigma = np.sqrt(w @ cov.values @ w)
            mrc = (cov.values @ w) / sigma if sigma > 0 else np.zeros(n)
            rc = w * mrc
            diff = rc - rc.mean()
            if np.max(np.abs(diff)) < 1e-6:
                break
            # Simple gradient step
            w = w - 0.1 * diff
            w = np.maximum(w, 0)
            w = w / w.sum() if w.sum() > 0 else np.ones(n) / n
        return pd.Series(w, index=cov.index)
