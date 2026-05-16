
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from portfolio_optimization.covariance import CovarianceEstimator
from portfolio_optimization.correlation import CorrelationAnalyzer
from portfolio_optimization.volatility_targeting import VolatilityTargeting
from portfolio_optimization.risk_parity import RiskParityAllocator
from portfolio_optimization.constraints import Constraints

class AllocationEngine:
    def __init__(self,
                 cov_estimator: Optional[CovarianceEstimator] = None,
                 corr_analyzer: Optional[CorrelationAnalyzer] = None,
                 vol_target: Optional[VolatilityTargeting] = None,
                 allocator: Optional[RiskParityAllocator] = None,
                 constraints: Optional[Constraints] = None):
        self.cov_estimator = cov_estimator or CovarianceEstimator()
        self.corr_analyzer = corr_analyzer or CorrelationAnalyzer()
        self.vol_target = vol_target or VolatilityTargeting()
        self.allocator = allocator or RiskParityAllocator()
        self.constraints = constraints or Constraints()

    def allocate(self,
                 signals: Dict[str, float],
                 returns_df: pd.DataFrame,
                 current_positions: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        symbols = list(signals.keys())
        sub_returns = returns_df[symbols] if all(s in returns_df.columns for s in symbols) else returns_df
        cov = self.cov_estimator.estimate(sub_returns)
        corr = self.corr_analyzer.compute(sub_returns)
        high_corr = self.corr_analyzer.high_correlation_pairs(corr)
        # Base allocation from risk parity on covariance
        weights = self.allocator.allocate(cov)
        # Directional overlay from signals
        signal_series = pd.Series(signals)
        aligned_signal = signal_series.reindex(weights.index).fillna(0)
        # Blend: risk parity weights * signal sign
        directional = weights * np.sign(aligned_signal)
        # Apply volatility targeting
        if len(sub_returns) > 0:
            portfolio_returns = (sub_returns * directional.reindex(sub_returns.columns).fillna(0)).sum(axis=1)
            scaled = self.vol_target.apply(directional, portfolio_returns)
        else:
            scaled = directional
        # Apply constraints
        final_weights = self.constraints.apply(scaled, high_corr)
        # Notional
        notional = final_weights  # assuming unit capital
        order_intents = {}
        if current_positions:
            for sym in symbols:
                current = current_positions.get(sym, 0.0)
                target = final_weights.get(sym, 0.0)
                delta = target - current
                if abs(delta) > 1e-6:
                    order_intents[sym] = round(float(delta), 6)
        return {
            "target_weights": final_weights.to_dict(),
            "target_notional": notional.to_dict(),
            "order_intents": order_intents,
            "covariance_valid": self.cov_estimator.is_valid(cov),
            "high_correlation_pairs": high_corr,
            "volatility_scalar": self.vol_target.compute_scalar(portfolio_returns) if len(sub_returns) > 0 else 1.0
        }
