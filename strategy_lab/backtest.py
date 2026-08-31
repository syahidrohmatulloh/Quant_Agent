"""
Simple vectorized/deterministic backtest engine.
Paper-only. No live trading. No profitability guarantees.
"""
from typing import Dict, Any, List
from strategies.base import BaseStrategy


def _compute_returns(equity: List[float]) -> List[float]:
    return [
        (equity[i] - equity[i - 1]) / equity[i - 1]
        for i in range(1, len(equity))
        if equity[i - 1] != 0
    ] if len(equity) > 1 else []


class SimpleBacktestEngine:
    """
    Walk-bar deterministic backtest.
    Assumes one signal per bar per symbol; applies signal at next bar open.

    cash_balance contains realized cash only.
    equity = cash_balance + current unrealized PnL.
    """

    def __init__(
        self,
        data: Dict[str, List[Dict[str, Any]]],
        strategy: BaseStrategy,
        initial_balance: float = 100000.0,
        commission_rate: float = 0.0001,
    ):
        self.data = data
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate
        self.equity_curve: List[float] = [initial_balance]
        self.trades: List[Dict[str, Any]] = []

    def _commission(self, price: float, volume: float) -> float:
        """Commission as a rate of traded notional for this generic engine."""
        return abs(price * volume) * self.commission_rate

    def _open_position(self, positions, sym, direction, price, volume=1.0):
        entry_commission = self._commission(price, volume)
        positions[sym] = {
            "direction": direction,
            "entry_price": price,
            "volume": volume,
            "entry_commission": entry_commission,
        }
        return entry_commission

    def _close_position(self, positions, sym, price):
        pos = positions[sym]
        if pos["direction"] == "long":
            gross_pnl = (price - pos["entry_price"]) * pos["volume"]
        else:
            gross_pnl = (pos["entry_price"] - price) * pos["volume"]

        exit_commission = self._commission(price, pos["volume"])
        net_trade_pnl = gross_pnl - pos["entry_commission"] - exit_commission
        cash_delta = gross_pnl - exit_commission

        self.trades.append({
            "symbol": sym,
            "direction": pos["direction"],
            "entry": pos["entry_price"],
            "exit": price,
            "gross_pnl": round(gross_pnl, 8),
            "commission": round(pos["entry_commission"] + exit_commission, 8),
            "pnl": round(net_trade_pnl, 8),
        })
        del positions[sym]
        return cash_delta

    def run(self) -> Dict[str, Any]:
        min_bars = min(len(v) for v in self.data.values()) if self.data else 0
        if min_bars < 2:
            return self._empty_result()

        cash_balance = self.initial_balance
        positions: Dict[str, Dict[str, Any]] = {}
        timestamps = []

        for i in range(1, min_bars):
            slice_data = {sym: bars[:i] for sym, bars in self.data.items()}
            result = self.strategy.generate(slice_data)
            current_bars = {sym: self.data[sym][i] for sym in self.data}
            ts = list(current_bars.values())[0]["timestamp"]
            timestamps.append(ts)

            for sig in result.signals:
                sym = sig.symbol
                bar = current_bars.get(sym)
                if not bar:
                    continue
                price = bar["open"]

                if sig.signal in ("long", "buy"):
                    if sym in positions and positions[sym]["direction"] == "short":
                        cash_balance += self._close_position(positions, sym, price)
                    if sym not in positions:
                        cash_balance -= self._open_position(positions, sym, "long", price)

                elif sig.signal in ("short", "sell"):
                    if sym in positions and positions[sym]["direction"] == "long":
                        cash_balance += self._close_position(positions, sym, price)
                    if sym not in positions:
                        cash_balance -= self._open_position(positions, sym, "short", price)

                elif sig.signal in ("flat", "close") and sym in positions:
                    cash_balance += self._close_position(positions, sym, price)

            unrealized = 0.0
            for sym, pos in positions.items():
                close_price = current_bars[sym]["close"]
                if pos["direction"] == "long":
                    unrealized += (close_price - pos["entry_price"]) * pos["volume"]
                else:
                    unrealized += (pos["entry_price"] - close_price) * pos["volume"]

            equity = cash_balance + unrealized
            self.equity_curve.append(equity)

        return self._summarize(timestamps)

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "total_return": 0.0,
            "volatility": 0.0,
            "max_drawdown": 0.0,
            "hit_rate": 0.0,
            "total_trades": 0,
            "equity_curve": [self.initial_balance],
            "trades": [],
        }

    def _summarize(self, timestamps: List[Any]) -> Dict[str, Any]:
        returns = _compute_returns(self.equity_curve)
        total_return = (
            (self.equity_curve[-1] - self.initial_balance) / self.initial_balance
            if self.equity_curve else 0.0
        )
        if returns:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5 * (252 ** 0.5)
        else:
            volatility = 0.0

        peak = self.equity_curve[0]
        max_dd = 0.0
        for val in self.equity_curve:
            if val > peak:
                peak = val
            if peak:
                dd = (peak - val) / peak
                if dd > max_dd:
                    max_dd = dd

        wins = sum(1 for t in self.trades if t.get("pnl", 0) > 0)
        hit_rate = wins / len(self.trades) if self.trades else 0.0
        return {
            "total_return": round(total_return, 4),
            "volatility": round(volatility, 4),
            "max_drawdown": round(max_dd, 4),
            "hit_rate": round(hit_rate, 4),
            "total_trades": len(self.trades),
            "equity_curve": [round(e, 8) for e in self.equity_curve],
            "trades": self.trades,
            "timestamps": [str(t) for t in timestamps],
        }
