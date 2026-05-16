
import numpy as np
import pandas as pd
from typing import Optional

class CovarianceEstimator:
    def __init__(self, method: str = "sample", halflife: int = 30):
        self.method = method
        self.halflife = halflife

    def estimate(self, returns: pd.DataFrame) -> pd.DataFrame:
        if returns.empty or returns.isna().all().all():
            raise ValueError("Returns data is empty or all NaN")
        if self.method == "sample":
            return returns.cov()
        elif self.method == "ewm":
            span = (2 * self.halflife) - 1
            ewm_cov = returns.ewm(span=span).cov()
            # ewm_cov is a MultiIndex; take the last panel
            if isinstance(ewm_cov.index, pd.MultiIndex):
                last_date = ewm_cov.index.get_level_values(0).max()
                return ewm_cov.loc[last_date]
            return ewm_cov
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def is_valid(self, cov: pd.DataFrame) -> bool:
        if cov.isna().any().any():
            return False
        # Check positive semi-definite roughly
        eigvals = np.linalg.eigvals(cov.values)
        return bool(np.all(eigvals >= -1e-8))
