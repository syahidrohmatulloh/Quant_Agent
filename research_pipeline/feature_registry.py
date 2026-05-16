
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

@dataclass
class FeatureSpec:
    feature_name: str
    version: str
    formula: str
    lookback_window: int
    required_columns: List[str]
    no_lookahead: bool = True

class FeatureRegistry:
    def __init__(self):
        self._features: Dict[str, FeatureSpec] = {}
        self._calculators: Dict[str, Callable] = {}

    def register(self, spec: FeatureSpec, calculator: Callable):
        key = f"{spec.feature_name}_{spec.version}"
        self._features[key] = spec
        self._calculators[key] = calculator

    def get(self, feature_name: str, version: str) -> FeatureSpec:
        key = f"{feature_name}_{version}"
        if key not in self._features:
            raise KeyError(f"Feature {key} not registered")
        return self._features[key]

    def calculate(self, feature_name: str, version: str, df: Any) -> Any:
        key = f"{feature_name}_{version}"
        if key not in self._calculators:
            raise KeyError(f"Calculator for {key} not found")
        spec = self._features[key]
        for col in spec.required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column {col} missing")
        return self._calculators[key](df)

    def list_features(self) -> List[str]:
        return list(self._features.keys())

    def validate_no_lookahead(self, feature_name: str, version: str) -> bool:
        spec = self.get(feature_name, version)
        return spec.no_lookahead
