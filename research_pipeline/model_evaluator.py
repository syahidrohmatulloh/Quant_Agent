
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class EvaluationResult:
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: List[List[int]]
    overfitting_warning: bool
    out_of_sample: bool
    notes: str

class ModelEvaluator:
    def __init__(self):
        pass

    def evaluate(self, y_true: pd.Series, y_pred: np.ndarray,
                 out_of_sample: bool = False) -> EvaluationResult:
        # Align
        aligned = pd.concat([y_true, pd.Series(y_pred, index=y_true.index)], axis=1).dropna()
        if aligned.empty:
            return EvaluationResult(0, 0, 0, 0, [[0, 0], [0, 0]], False, out_of_sample, "No aligned data")
        yt = aligned.iloc[:, 0].astype(int)
        yp = aligned.iloc[:, 1].astype(int)

        cm = self._confusion_matrix(yt, yp)
        tp, fp, fn, tn = cm[1][1], cm[0][1], cm[1][0], cm[0][0]
        accuracy = (tp + tn) / len(yt) if len(yt) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        # Overfitting warning: if accuracy > 95% on in-sample
        overfitting = (not out_of_sample) and accuracy > 0.95

        return EvaluationResult(
            accuracy=round(accuracy, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            confusion_matrix=cm,
            overfitting_warning=overfitting,
            out_of_sample=out_of_sample,
            notes=""
        )

    def _confusion_matrix(self, y_true: pd.Series, y_pred: pd.Series) -> List[List[int]]:
        classes = sorted(set(y_true.unique()) | set(y_pred.unique()))
        if len(classes) == 0:
            return [[0, 0], [0, 0]]
        # Simplify to binary if possible
        if set(classes).issubset({0, 1, -1}):
            # Map -1 to 0 for binary
            yt = y_true.replace(-1, 0).astype(int)
            yp = y_pred.replace(-1, 0).astype(int)
            tp = ((yt == 1) & (yp == 1)).sum()
            fp = ((yt == 0) & (yp == 1)).sum()
            fn = ((yt == 1) & (yp == 0)).sum()
            tn = ((yt == 0) & (yp == 0)).sum()
            return [[int(tn), int(fp)], [int(fn), int(tp)]]
        # Multi-class fallback (simplified)
        return [[0, 0], [0, 0]]

    def backtest_evaluate(self, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        if not trades:
            return {"total_return": 0.0, "win_rate": 0.0}
        returns = [t.get("pnl", 0) for t in trades]
        win_rate = sum(1 for r in returns if r > 0) / len(returns)
        total_return = sum(returns)
        return {"total_return": round(total_return, 2), "win_rate": round(win_rate, 4)}
