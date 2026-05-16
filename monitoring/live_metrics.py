
from typing import Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class LiveMetrics:
    signals_generated: int = 0
    signals_rejected: int = 0
    orders_created: int = 0
    wins: int = 0
    losses: int = 0
    current_exposure: float = 0.0
    current_drawdown: float = 0.0
    rejected_by_reason: Dict[str, int] = field(default_factory=dict)
    model_predictions: List[float] = field(default_factory=list)

    def record_signal(self, generated: bool, reason: str = ""):
        if generated:
            self.signals_generated += 1
        else:
            self.signals_rejected += 1
            self.rejected_by_reason[reason] = self.rejected_by_reason.get(reason, 0) + 1

    def record_order(self):
        self.orders_created += 1

    def record_prediction(self, pred: float):
        self.model_predictions.append(pred)

    def record_pnl(self, pnl: float):
        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1

    def update_exposure(self, exposure: float):
        self.current_exposure = exposure

    def update_drawdown(self, dd: float):
        self.current_drawdown = dd

    def summary(self) -> Dict[str, Any]:
        total = self.wins + self.losses
        return {
            "signals_generated": self.signals_generated,
            "signals_rejected": self.signals_rejected,
            "orders_created": self.orders_created,
            "win_rate": self.wins / total if total > 0 else 0.0,
            "current_exposure": round(self.current_exposure, 4),
            "current_drawdown": round(self.current_drawdown, 4),
            "rejected_by_reason": self.rejected_by_reason,
            "prediction_mean": sum(self.model_predictions) / len(self.model_predictions) if self.model_predictions else 0.0
        }
