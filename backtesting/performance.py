
import math
from typing import List, Dict, Any

class PerformanceAnalyzer:
    def __init__(self, trades: List[Dict[str, Any]], equity_curve: List[float], timestamps: List[str]):
        self.trades = trades
        self.equity_curve = equity_curve
        self.timestamps = timestamps

    def sharpe(self, risk_free_rate: float = 0.0) -> float:
        if len(self.equity_curve) < 2:
            return 0.0
        returns = []
        for i in range(1, len(self.equity_curve)):
            r = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            returns.append(r)
        if not returns:
            return 0.0
        avg = sum(returns) / len(returns)
        std = math.sqrt(sum((r - avg) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 0.0
        if std == 0:
            return 0.0
        return (avg - risk_free_rate) / std * math.sqrt(252)  # annualized

    def sortino(self, risk_free_rate: float = 0.0) -> float:
        if len(self.equity_curve) < 2:
            return 0.0
        returns = []
        for i in range(1, len(self.equity_curve)):
            r = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            returns.append(r)
        if not returns:
            return 0.0
        avg = sum(returns) / len(returns)
        downside = [r for r in returns if r < risk_free_rate]
        downside_std = math.sqrt(sum((r - risk_free_rate) ** 2 for r in downside) / len(downside)) if downside else 0.0
        if downside_std == 0:
            return 0.0
        return (avg - risk_free_rate) / downside_std * math.sqrt(252)

    def calmar(self) -> float:
        if not self.equity_curve:
            return 0.0
        total_return = (self.equity_curve[-1] - self.equity_curve[0]) / self.equity_curve[0]
        max_dd = self.max_drawdown()
        if max_dd == 0:
            return 0.0
        return total_return / max_dd

    def max_drawdown(self) -> float:
        peak = self.equity_curve[0]
        max_dd = 0.0
        for val in self.equity_curve:
            if val > peak:
                peak = val
            dd = (peak - val) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.get("pnl", 0) > 0)
        return wins / len(self.trades)

    def expectancy(self) -> float:
        if not self.trades:
            return 0.0
        return sum(t.get("pnl", 0) for t in self.trades) / len(self.trades)

    def summary(self) -> Dict[str, Any]:
        return {
            "total_trades": len(self.trades),
            "win_rate": round(self.win_rate(), 4),
            "expectancy": round(self.expectancy(), 4),
            "sharpe": round(self.sharpe(), 4),
            "sortino": round(self.sortino(), 4),
            "calmar": round(self.calmar(), 4),
            "max_drawdown": round(self.max_drawdown(), 4),
            "final_equity": round(self.equity_curve[-1], 2) if self.equity_curve else 0.0
        }
