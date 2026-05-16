
import pandas as pd
from typing import Dict, Any, Optional, List
from research_pipeline.feature_registry import FeatureRegistry

class FeatureRuntime:
    def __init__(self, registry: FeatureRegistry, min_lookback: int = 50):
        self.registry = registry
        self.min_lookback = min_lookback

    def compute(self, data: pd.DataFrame, feature_set_id: str) -> Optional[Dict[str, Any]]:
        # feature_set_id format: feature1_v1,feature2_v1
        features = feature_set_id.split(",")
        result = {}
        warnings = []
        for feat in features:
            parts = feat.split("_")
            if len(parts) < 2:
                warnings.append(f"Invalid feature id: {feat}")
                continue
            version = parts[-1]
            name = "_".join(parts[:-1])
            try:
                spec = self.registry.get(name, version)
                if spec.lookback_window > len(data):
                    warnings.append(f"Insufficient lookback for {feat}: need {spec.lookback_window}, have {len(data)}")
                    continue
                val = self.registry.calculate(name, version, data)
                result[feat] = val.iloc[-1] if hasattr(val, "iloc") else val
            except Exception as e:
                warnings.append(f"Error computing {feat}: {str(e)}")
        if warnings:
            return {
                "feature_vector": result,
                "feature_set_id": feature_set_id,
                "timestamp": str(data.index[-1]) if len(data) > 0 else None,
                "warnings": warnings,
                "valid": len(result) > 0
            }
        return {
            "feature_vector": result,
            "feature_set_id": feature_set_id,
            "timestamp": str(data.index[-1]) if len(data) > 0 else None,
            "warnings": [],
            "valid": True
        }

    def validate_lookahead(self, data: pd.DataFrame) -> bool:
        # Check if any column name contains forbidden lookahead keywords
        forbidden = {"future", "next", "target", "label"}
        cols = [c.lower() for c in data.columns]
        for col in cols:
            for f in forbidden:
                if f in col:
                    return False
        return True
