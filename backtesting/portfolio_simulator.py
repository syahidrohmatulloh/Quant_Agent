
from typing import Dict, List
from backtesting.event import FillEvent, PositionClosedEvent

class PortfolioSimulator:
    def __init__(self, initial_balance: float = 100000.0):
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.equity = initial_balance
        self.positions: Dict[str, Dict] = {}
        self.trades: List[Dict] = []
        self.peak_equity = initial_balance
        self.max_drawdown = 0.0

    def on_fill(self, fill: FillEvent):
        cost = fill.fill_price * fill.volume * 100000  # FX lot size approximation
        margin = cost / 100  # 1% margin at 100:1 leverage
        self.cash -= margin
        pos_key = f"{fill.symbol}_{fill.direction}"
        if pos_key not in self.positions:
            self.positions[pos_key] = {
                "symbol": fill.symbol,
                "direction": fill.direction,
                "volume": fill.volume,
                "entry_price": fill.fill_price,
                "commission": fill.commission
            }
        else:
            self.positions[pos_key]["volume"] += fill.volume
            # simplistic averaging
            old_vol = self.positions[pos_key]["volume"] - fill.volume
            old_px = self.positions[pos_key]["entry_price"]
            self.positions[pos_key]["entry_price"] = (old_px * old_vol + fill.fill_price * fill.volume) / self.positions[pos_key]["volume"]
            self.positions[pos_key]["commission"] += fill.commission

    def on_position_closed(self, event: PositionClosedEvent):
        self.cash += event.pnl + (event.entry_price * event.volume * 100000 / 100)
        self.trades.append({
            "symbol": event.symbol,
            "direction": event.direction,
            "volume": event.volume,
            "entry_price": event.entry_price,
            "exit_price": event.exit_price,
            "pnl": event.pnl,
            "commission": event.commission
        })
        self.equity = self.cash + sum(self._unrealized(p) for p in self.positions.values())
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        dd = (self.peak_equity - self.equity) / self.peak_equity
        if dd > self.max_drawdown:
            self.max_drawdown = dd

    def _unrealized(self, pos):
        # placeholder; updated by engine
        return 0.0

    def update_equity(self, current_prices: Dict[str, float]):
        unrealized = 0.0
        for pos in self.positions.values():
            price = current_prices.get(pos["symbol"], pos["entry_price"])
            if pos["direction"] == "buy":
                unrealized += (price - pos["entry_price"]) * pos["volume"] * 100000
            else:
                unrealized += (pos["entry_price"] - price) * pos["volume"] * 100000
        self.equity = self.cash + unrealized
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        dd = (self.peak_equity - self.equity) / self.peak_equity
        if dd > self.max_drawdown:
            self.max_drawdown = dd
