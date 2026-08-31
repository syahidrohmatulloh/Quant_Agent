import math
from datetime import datetime
from statistics import median
from typing import List, Dict, Any, Optional


class PerformanceAnalyzer:
    def __init__(
        self,
        trades: List[Dict[str, Any]],
        equity_curve: List[float],
        timestamps: List[str],
        periods_per_year: Optional[float] = None,
    ):
        self.trades = trades
        self.equity_curve = equity_curve
        self.timestamps = timestamps
        self.periods_per_year = periods_per_year or self._infer_periods_per_year()

    def _infer_periods_per_year(self) -> float:
        """Infer an annualization factor from timestamp spacing.

        Uses a 252-trading-day convention for intraday/daily market data.
        Falls back to 252 when timestamps are unavailable or unparseable.
        """
        parsed = []
        for value in self.timestamps:
            if isinstance(value, datetime):
                parsed.append(value)
                continue
            try:
                parsed.append(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
            except (TypeError, ValueError):
                continue

        if len(parsed) < 2:
            return 252.0

        deltas = [
            (parsed[i] - parsed[i - 1]).total_seconds()
            for i in range(1, len(parsed))
            if (parsed[i] - parsed[i - 1]).total_seconds() > 0
        ]
        if not deltas:
            return 252.0

        seconds = median(deltas)
        if seconds >= 25 * 24 * 3600:
            return 12.0
        if seconds >= 6 * 24 * 3600:
            return 52.0
        return max(1.0, (252.0 * 24.0 * 3600.0) / seconds)

    def _returns(self) -> List[float]:
        returns = []
        for i in range(1, len(self.equity_curve)):
            previous = self.equity_curve[i - 1]
            if previous == 0:
                continue
            returns.append((self.equity_curve[i] - previous) / previous)
        return returns

    def sharpe(self, risk_free_rate: float = 0.0) -> float:
        returns = self._returns()
        if not returns:
            return 0.0
        avg = sum(returns) / len(returns)
        std = (
            math.sqrt(sum((r - avg) ** 2 for r in returns) / len(returns))
            if len(returns) > 1 else 0.0
        )
        if std == 0:
            return 0.0
        return (avg - risk_free_rate) / std * math.sqrt(self.periods_per_year)

    def sortino(self, risk_free_rate: float = 0.0) -> float:
        returns = self._returns()
        if not returns:
            return 0.0
        avg = sum(returns) / len(returns)
        downside = [r for r in returns if r < risk_free_rate]
        downside_std = (
            math.sqrt(sum((r - risk_free_rate) ** 2 for r in downside) / len(downside))
            if downside else 0.0
        )
        if downside_std == 0:
            return 0.0
        return (avg - risk_free_rate) / downside_std * math.sqrt(self.periods_per_year)

    def calmar(self) -> float:
        if len(self.equity_curve) < 2 or self.equity_curve[0] <= 0:
            return 0.0
        max_dd = self.max_drawdown()
        if max_dd == 0:
            return 0.0

        periods = max(1, len(self.equity_curve) - 1)
        years = periods / self.periods_per_year if self.periods_per_year > 0 else 0.0
        if years <= 0 or self.equity_curve[-1] <= 0:
            return 0.0
        annualized_return = (self.equity_curve[-1] / self.equity_curve[0]) ** (1.0 / years) - 1.0
        return annualized_return / max_dd

    def max_drawdown(self) -> float:
        if not self.equity_curve:
            return 0.0
        peak = self.equity_curve[0]
        max_dd = 0.0
        for val in self.equity_curve:
            if val > peak:
                peak = val
            if peak <= 0:
                continue
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
            "final_equity": round(self.equity_curve[-1], 2) if self.equity_curve else 0.0,
            "periods_per_year": round(self.periods_per_year, 4),
        }
