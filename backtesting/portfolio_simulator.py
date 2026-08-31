from typing import Dict, List
from backtesting.event import FillEvent, PositionClosedEvent


CONTRACT_SIZE = 100000.0
MARGIN_RATE = 0.01


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
        notional = fill.fill_price * fill.volume * CONTRACT_SIZE
        margin = notional * MARGIN_RATE
        self.cash -= margin

        pos_key = f"{fill.symbol}_{fill.direction}"
        if pos_key not in self.positions:
            self.positions[pos_key] = {
                "symbol": fill.symbol,
                "direction": fill.direction,
                "volume": fill.volume,
                "entry_price": fill.fill_price,
                "commission": fill.commission,
                "margin": margin,
                "last_price": fill.fill_price,
            }
        else:
            pos = self.positions[pos_key]
            old_vol = pos["volume"]
            new_vol = old_vol + fill.volume
            pos["entry_price"] = (
                pos["entry_price"] * old_vol + fill.fill_price * fill.volume
            ) / new_vol
            pos["volume"] = new_vol
            pos["commission"] += fill.commission
            pos["margin"] += margin
            pos["last_price"] = fill.fill_price

    def on_position_closed(self, event: PositionClosedEvent):
        pos_key = f"{event.symbol}_{event.direction}"
        position = self.positions.pop(pos_key, None)

        if position is not None:
            margin_release = float(position.get("margin", 0.0))
        else:
            margin_release = event.entry_price * event.volume * CONTRACT_SIZE * MARGIN_RATE

        self.cash += event.pnl + margin_release
        self.trades.append({
            "symbol": event.symbol,
            "direction": event.direction,
            "volume": event.volume,
            "entry_price": event.entry_price,
            "exit_price": event.exit_price,
            "pnl": event.pnl,
            "commission": event.commission,
        })
        self._refresh_equity()

    def _unrealized(self, pos):
        price = pos.get("last_price", pos["entry_price"])
        if pos["direction"] == "buy":
            return (price - pos["entry_price"]) * pos["volume"] * CONTRACT_SIZE
        return (pos["entry_price"] - price) * pos["volume"] * CONTRACT_SIZE

    def _refresh_equity(self):
        self.equity = self.cash + sum(self._unrealized(p) for p in self.positions.values())
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        if self.peak_equity > 0:
            dd = (self.peak_equity - self.equity) / self.peak_equity
            if dd > self.max_drawdown:
                self.max_drawdown = dd

    def update_equity(self, current_prices: Dict[str, float]):
        for pos in self.positions.values():
            if pos["symbol"] in current_prices:
                pos["last_price"] = current_prices[pos["symbol"]]
        self._refresh_equity()
