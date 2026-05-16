
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class ModelOutput:
    predictions: np.ndarray
    confidence: np.ndarray
    model_version: str
    model_id: str

class SimpleRuleModel:
    """Mock model when sklearn is unavailable. Uses simple rule-based logic."""
    def __init__(self, feature_weights: Optional[Dict[str, float]] = None):
        self.feature_weights = feature_weights or {}
        self.classes_ = np.array([0, 1])

    def fit(self, X: pd.DataFrame, y: pd.Series):
        # Simple heuristic: weight features by correlation with target
        for col in X.columns:
            if X[col].std() > 0:
                self.feature_weights[col] = np.corrcoef(X[col].fillna(0), y.fillna(0))[0, 1]
        self.classes_ = np.unique(y.dropna())

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        scores = np.zeros(len(X))
        for col, w in self.feature_weights.items():
            scores += X[col].fillna(0).values * w
        return np.where(scores > 0, 1, 0)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.predict(X)
        proba = np.zeros((len(X), 2))
        proba[:, 0] = np.where(preds == 0, 0.7, 0.3)
        proba[:, 1] = np.where(preds == 1, 0.7, 0.3)
        return proba

class ModelTrainer:
    def __init__(self, model_type: str = "simple_rule"):
        self.model_type = model_type
        self.model = None
        self.feature_names: List[str] = []
        self._try_sklearn()

    def _try_sklearn(self):
        if self.model_type == "logistic_regression":
            try:
                from sklearn.linear_model import LogisticRegression
                self.model = LogisticRegression(max_iter=1000)
            except ImportError:
                self.model = SimpleRuleModel()
                self.model_type = "simple_rule"
        else:
            self.model = SimpleRuleModel()

    def train(self, X: pd.DataFrame, y: pd.Series,
              model_id: str = "", model_version: str = "v1") -> ModelOutput:
        self.feature_names = list(X.columns)
        X_clean = X.fillna(0)
        y_clean = y.dropna()
        # Align
        aligned = pd.concat([X_clean, y_clean], axis=1).dropna()
        if aligned.empty:
            return ModelOutput(
                predictions=np.array([]),
                confidence=np.array([]),
                model_version=model_version,
                model_id=model_id
            )
        X_train = aligned.iloc[:, :-1]
        y_train = aligned.iloc[:, -1]
        self.model.fit(X_train, y_train)
        preds = self.model.predict(X_train)
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X_train)
            conf = proba.max(axis=1)
        else:
            conf = np.ones(len(preds)) * 0.5
        return ModelOutput(
            predictions=preds,
            confidence=conf,
            model_version=model_version,
            model_id=model_id
        )

    def predict(self, X: pd.DataFrame) -> ModelOutput:
        X_clean = X[self.feature_names].fillna(0)
        preds = self.model.predict(X_clean)
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X_clean)
            conf = proba.max(axis=1)
        else:
            conf = np.ones(len(preds)) * 0.5
        return ModelOutput(
            predictions=preds,
            confidence=conf,
            model_version="v1",
            model_id=""
        )
