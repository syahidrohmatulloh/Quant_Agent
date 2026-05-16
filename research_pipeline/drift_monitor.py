
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class DriftReport:
    feature_drift: Dict[str, float]
    prediction_drift: float
    performance_drift: float
    data_quality: Dict[str, Any]
    missing_rate: float
    spread_regime: str
    alert: bool

class DriftMonitor:
    def __init__(self, reference_features: pd.DataFrame,
                 reference_predictions: Optional[np.ndarray] = None):
        self.reference_features = reference_features
        self.reference_predictions = reference_predictions
        self.reference_mean = reference_features.mean()
        self.reference_std = reference_features.std().replace(0, 1e-9)

    def check(self, new_features: pd.DataFrame,
              new_predictions: Optional[np.ndarray] = None,
              new_performance: Optional[float] = None) -> DriftReport:
        # Feature drift: normalized mean shift
        feature_drift = {}
        for col in self.reference_features.columns:
            if col in new_features.columns:
                shift = abs(new_features[col].mean() - self.reference_mean[col]) / self.reference_std[col]
                feature_drift[col] = round(float(shift), 4)

        # Prediction drift
        pred_drift = 0.0
        if self.reference_predictions is not None and new_predictions is not None:
            pred_drift = abs(np.mean(new_predictions) - np.mean(self.reference_predictions))

        # Performance drift
        perf_drift = 0.0
        if new_performance is not None:
            perf_drift = new_performance  # placeholder

        # Data quality
        missing_rate = float(new_features.isna().mean().mean())
        data_quality = {
            "rows": len(new_features),
            "missing_cells": int(new_features.isna().sum().sum()),
            "columns": list(new_features.columns)
        }

        # Spread regime (placeholder)
        spread_regime = "normal"

        # Alert if any feature drift > 3 sigma or missing rate > 10%
        alert = bool(any(v > 3.0 for v in feature_drift.values()) or missing_rate > 0.1)

        return DriftReport(
            feature_drift=feature_drift,
            prediction_drift=round(float(pred_drift), 4),
            performance_drift=round(float(perf_drift), 4),
            data_quality=data_quality,
            missing_rate=round(missing_rate, 4),
            spread_regime=spread_regime,
            alert=alert
        )
