
import pandas as pd
from typing import Dict, Any, Optional

class RebalanceEngine:
    def __init__(self, threshold: float = 0.02, min_trade: float = 0.001):
        self.threshold = threshold
        self.min_trade = min_trade

    def should_rebalance(self, current: Dict[str, float], target: Dict[str, float]) -> bool:
        all_symbols = set(current.keys()) | set(target.keys())
        for sym in all_symbols:
            diff = abs(target.get(sym, 0.0) - current.get(sym, 0.0))
            if diff > self.threshold:
                return True
        return False

    def generate_orders(self,
                        current: Dict[str, float],
                        target: Dict[str, float]) -> Dict[str, Any]:
        orders = {}
        all_symbols = set(current.keys()) | set(target.keys())
        for sym in all_symbols:
            delta = target.get(sym, 0.0) - current.get(sym, 0.0)
            if abs(delta) >= self.min_trade:
                orders[sym] = round(float(delta), 6)
        return {
            "rebalance_needed": len(orders) > 0,
            "orders": orders,
            "threshold": self.threshold,
            "min_trade": self.min_trade
        }

    def scheduled_rebalance(self,
                            current: Dict[str, float],
                            target: Dict[str, float],
                            force: bool = False) -> Dict[str, Any]:
        if force or self.should_rebalance(current, target):
            return self.generate_orders(current, target)
        return {"rebalance_needed": False, "orders": {}}
