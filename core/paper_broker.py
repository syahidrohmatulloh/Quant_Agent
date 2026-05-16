
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class PaperOrder:
    order_id: str
    symbol: str
    direction: str
    volume: float
    entry_price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    status: str = "open"

@dataclass
class PaperPosition:
    position_id: str
    order_id: str
    symbol: str
    direction: str
    volume: float
    entry_price: float
    current_price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    status: str = "open"
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

class PaperBroker:
    def __init__(self, balance: float = 100000.0, commission_per_lot: float = 7.0,
                 slippage_pips: float = 0.5, leverage: float = 100.0):
        self.balance = balance
        self.commission_per_lot = commission_per_lot
        self.slippage_pips = slippage_pips
        self.leverage = leverage
        self.orders: Dict[str, PaperOrder] = {}
        self.positions: Dict[str, PaperPosition] = {}
        self._order_counter = 0
        self._pos_counter = 0

    def _next_order_id(self):
        self._order_counter += 1
        return f"PAPER-ORDER-{self._order_counter:06d}"

    def _next_pos_id(self):
        self._pos_counter += 1
        return f"PAPER-POS-{self._pos_counter:06d}"

    def open_position(self, symbol: str, direction: str, volume: float,
                      price: float, sl: Optional[float] = None,
                      tp: Optional[float] = None) -> tuple:
        order_id = self._next_order_id()
        position_id = self._next_pos_id()
        order = PaperOrder(order_id=order_id, symbol=symbol, direction=direction,
                           volume=volume, entry_price=price, sl=sl, tp=tp)
        pos = PaperPosition(position_id=position_id, order_id=order_id,
                            symbol=symbol, direction=direction, volume=volume,
                            entry_price=price, current_price=price, sl=sl, tp=tp)
        self.orders[order_id] = order
        self.positions[position_id] = pos
        return order_id, position_id

    def close_position(self, position_id: str, price: float):
        pos = self.positions.get(position_id)
        if not pos or pos.status != "open":
            return None
        pos.status = "closed"
        pos.current_price = price
        if pos.direction == "buy":
            pos.realized_pnl = (price - pos.entry_price) * pos.volume * 100000
        else:
            pos.realized_pnl = (pos.entry_price - price) * pos.volume * 100000
        pos.unrealized_pnl = 0.0
        commission = self.commission_per_lot * pos.volume
        pos.realized_pnl -= commission
        self.balance += pos.realized_pnl
        return pos

    def update_prices(self, symbol: str, bid: float, ask: float):
        for pos in self.positions.values():
            if pos.symbol == symbol and pos.status == "open":
                pos.current_price = ask if pos.direction == "buy" else bid
                if pos.direction == "buy":
                    pos.unrealized_pnl = (pos.current_price - pos.entry_price) * pos.volume * 100000
                else:
                    pos.unrealized_pnl = (pos.entry_price - pos.current_price) * pos.volume * 100000
