"""
Simple vectorized/deterministic backtest engine.
Paper-only. No live trading. No profitability guarantees.
"""
from typing import Dict, Any, List
from strategies.base import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult


def _compute_returns(equity: List[float]) -> List[float]:
    return [(equity[i] - equity[i - 1]) / equity[i - 1] for i in range(1, len(equity))] if len(equity) > 1 else []


class SimpleBacktestEngine:
    """
    Walk-bar deterministic backtest.
    Assumes one signal per bar per symbol; applies signal at next bar open.
    """

    def __init__(self, data: Dict[str, List[Dict[str, Any]]], strategy: BaseStrategy,
                 initial_balance: float = 100000.0, commission_rate: float = 0.0001):
        self.data = data
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate
        self.equity_curve: List[float] = [initial_balance]
        self.trades: List[Dict[str, Any]] = []

    def run(self) -> Dict[str, Any]:
        # Determine common bar count (minimum across symbols)
        min_bars = min(len(v) for v in self.data.values()) if self.data else 0
        if min_bars < 2:
            return self._empty_result()
        balance = self.initial_balance
        positions: Dict[str, Dict[str, Any]] = {}  # symbol -> {direction, entry_price, volume}
        timestamps = []
        for i in range(1, min_bars):
            # Build slice up to i for strategy
            slice_data = {sym: bars[:i] for sym, bars in self.data.items()}
            result = self.strategy.generate(slice_data)
            # Apply signals at open of bar i
            current_bars = {sym: self.data[sym][i] for sym in self.data}
            ts = list(current_bars.values())[0]["timestamp"]
            timestamps.append(ts)
            pnl_step = 0.0
            for sig in result.signals:
                sym = sig.symbol
                bar = current_bars.get(sym)
                if not bar:
                    continue
                price = bar["open"]
                if sig.signal in ("long", "buy"):
                    # close existing short
                    if sym in positions and positions[sym]["direction"] == "short":
                        pnl = (positions[sym]["entry_price"] - price) * positions[sym]["volume"]
                        comm = abs(pnl) * self.commission_rate
                        pnl_step += pnl - comm
                        self.trades.append({"symbol": sym, "direction": "short", "entry": positions[sym]["entry_price"],
                                            "exit": price, "pnl": round(pnl - comm, 4)})
                        del positions[sym]
                    positions[sym] = {"direction": "long", "entry_price": price, "volume": 1.0}
                elif sig.signal in ("short", "sell"):
                    if sym in positions and positions[sym]["direction"] == "long":
                        pnl = (price - positions[sym]["entry_price"]) * positions[sym]["volume"]
                        comm = abs(pnl) * self.commission_rate
                        pnl_step += pnl - comm
                        self.trades.append({"symbol": sym, "direction": "long", "entry": positions[sym]["entry_price"],
                                            "exit": price, "pnl": round(pnl - comm, 4)})
                        del positions[sym]
                    positions[sym] = {"direction": "short", "entry_price": price, "volume": 1.0}
                elif sig.signal in ("flat", "close"):
                    if sym in positions:
                        pos = positions[sym]
                        if pos["direction"] == "long":
                            pnl = (price - pos["entry_price"]) * pos["volume"]
                        else:
                            pnl = (pos["entry_price"] - price) * pos["volume"]
                        comm = abs(pnl) * self.commission_rate
                        pnl_step += pnl - comm
                        self.trades.append({"symbol": sym, "direction": pos["direction"], "entry": pos["entry_price"],
                                            "exit": price, "pnl": round(pnl - comm, 4)})
                        del positions[sym]
            # Mark-to-market open positions at close
            for sym, pos in positions.items():
                close_price = current_bars[sym]["close"]
                if pos["direction"] == "long":
                    pnl_step += (close_price - pos["entry_price"]) * pos["volume"]
                else:
                    pnl_step += (pos["entry_price"] - close_price) * pos["volume"]
            balance += pnl_step
            self.equity_curve.append(balance)
        return self._summarize(timestamps)

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "total_return": 0.0,
            "volatility": 0.0,
            "max_drawdown": 0.0,
            "hit_rate": 0.0,
            "total_trades": 0,
            "equity_curve": [self.initial_balance],
            "trades": []
        }

    def _summarize(self, timestamps: List[Any]) -> Dict[str, Any]:
        returns = _compute_returns(self.equity_curve)
        total_return = (self.equity_curve[-1] - self.initial_balance) / self.initial_balance if self.equity_curve else 0.0
        volatility = (sum((r - sum(returns) / len(returns)) ** 2 for r in returns) / len(returns)) ** 0.5 * (252 ** 0.5) if returns else 0.0
        peak = self.equity_curve[0]
        max_dd = 0.0
        for val in self.equity_curve:
            if val > peak:
                peak = val
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
            "equity_curve": [round(e, 2) for e in self.equity_curve],
            "trades": self.trades,
            "timestamps": [str(t) for t in timestamps]
        }
