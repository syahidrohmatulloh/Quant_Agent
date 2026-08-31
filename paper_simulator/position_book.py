"""Position book for paper simulation.

Track positions by symbol/timeframe. Persist to local JSON. Never call broker.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

DEFAULT_CONTRACT_SIZE = 100000.0


class Position:
    """Represents a simulated position.

    realized_pnl and unrealized_pnl are gross price PnL.
    total_costs contains all simulated transaction costs exactly once.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        side: str,
        quantity: float,
        average_price: float,
        notional: float,
        realized_pnl: float = 0.0,
        unrealized_pnl: float = 0.0,
        total_costs: float = 0.0,
        opened_at: str = "",
        updated_at: str = "",
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.side = side
        self.quantity = quantity
        self.average_price = average_price
        self.notional = notional
        self.realized_pnl = realized_pnl
        self.unrealized_pnl = unrealized_pnl
        self.total_costs = total_costs
        self.opened_at = opened_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "side": self.side,
            "quantity": self.quantity,
            "average_price": self.average_price,
            "notional": self.notional,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "total_costs": self.total_costs,
            "opened_at": self.opened_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Position":
        return cls(
            symbol=d.get("symbol", ""),
            timeframe=d.get("timeframe", ""),
            side=d.get("side", "FLAT"),
            quantity=d.get("quantity", 0.0),
            average_price=d.get("average_price", 0.0),
            notional=d.get("notional", 0.0),
            realized_pnl=d.get("realized_pnl", 0.0),
            unrealized_pnl=d.get("unrealized_pnl", 0.0),
            total_costs=d.get("total_costs", 0.0),
            opened_at=d.get("opened_at", ""),
            updated_at=d.get("updated_at", ""),
        )


class PositionBook:
    """Track and manage simulated positions."""

    def __init__(self, state_path: str):
        self.state_path = state_path
        self.positions: Dict[str, Position] = {}
        self._load()

    def _key(self, symbol: str, timeframe: str) -> str:
        return symbol + "_" + timeframe

    def _load(self):
        p = Path(self.state_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.get("positions", {}).items():
                self.positions[k] = Position.from_dict(v)

    def save(self):
        p = Path(self.state_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "positions": {k: v.to_dict() for k, v in self.positions.items()},
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def get_position(self, symbol: str, timeframe: str) -> Optional[Position]:
        return self.positions.get(self._key(symbol, timeframe))

    @staticmethod
    def _side_from_fill(side: str) -> str:
        if side == "BUY":
            return "LONG"
        if side == "SELL":
            return "SHORT"
        return "FLAT"

    def update_position(
        self,
        symbol: str,
        timeframe: str,
        side: str,
        quantity: float,
        price: float,
        fill_cost: float,
    ) -> Position:
        """Update position after a fill. Handles open, increase, reduce, flip, flatten.

        Accounting invariant:
        net PnL = realized_gross + unrealized_gross - total_costs.
        """
        key = self._key(symbol, timeframe)
        now = datetime.now(timezone.utc).isoformat()
        existing = self.positions.get(key)

        side = str(side or "").upper()
        quantity = float(quantity or 0.0)
        price = float(price or 0.0)
        fill_cost = float(fill_cost or 0.0)

        if quantity < 0:
            raise ValueError("quantity must be non-negative")
        if price <= 0:
            raise ValueError("price must be positive")

        if existing is None:
            new_side = self._side_from_fill(side)
            pos = Position(
                symbol=symbol,
                timeframe=timeframe,
                side=new_side,
                quantity=quantity if new_side != "FLAT" else 0.0,
                average_price=price if new_side != "FLAT" else 0.0,
                notional=(quantity * price * DEFAULT_CONTRACT_SIZE) if new_side != "FLAT" else 0.0,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
                total_costs=fill_cost,
                opened_at=now,
                updated_at=now,
            )
            self.positions[key] = pos
            return pos

        if existing.side == "FLAT" or existing.quantity == 0:
            new_side = self._side_from_fill(side)
            existing.side = new_side
            existing.quantity = quantity if new_side != "FLAT" else 0.0
            existing.average_price = price if new_side != "FLAT" else 0.0
            existing.notional = (
                quantity * price * DEFAULT_CONTRACT_SIZE if new_side != "FLAT" else 0.0
            )
            existing.unrealized_pnl = 0.0
            existing.total_costs += fill_cost
            if new_side != "FLAT":
                existing.opened_at = now
            existing.updated_at = now
            return existing

        old_side = existing.side
        old_qty = existing.quantity
        old_avg = existing.average_price

        if side == "BUY" and old_side == "LONG":
            total_qty = old_qty + quantity
            weighted_value = old_qty * old_avg + quantity * price
            existing.quantity = total_qty
            existing.average_price = weighted_value / total_qty if total_qty > 0 else 0.0
            existing.notional = existing.quantity * existing.average_price * DEFAULT_CONTRACT_SIZE
            existing.total_costs += fill_cost

        elif side == "SELL" and old_side == "SHORT":
            total_qty = old_qty + quantity
            weighted_value = old_qty * old_avg + quantity * price
            existing.quantity = total_qty
            existing.average_price = weighted_value / total_qty if total_qty > 0 else 0.0
            existing.notional = existing.quantity * existing.average_price * DEFAULT_CONTRACT_SIZE
            existing.total_costs += fill_cost

        elif side == "SELL" and old_side == "LONG":
            closed_qty = min(quantity, old_qty)
            existing.realized_pnl += (price - old_avg) * closed_qty * DEFAULT_CONTRACT_SIZE
            existing.total_costs += fill_cost
            remaining = quantity - old_qty
            if remaining > 0:
                existing.side = "SHORT"
                existing.quantity = remaining
                existing.average_price = price
                existing.notional = remaining * price * DEFAULT_CONTRACT_SIZE
                existing.unrealized_pnl = 0.0
            else:
                existing.quantity = old_qty - quantity
                if existing.quantity > 0:
                    existing.notional = existing.quantity * old_avg * DEFAULT_CONTRACT_SIZE
                else:
                    existing.side = "FLAT"
                    existing.quantity = 0.0
                    existing.average_price = 0.0
                    existing.notional = 0.0
                    existing.unrealized_pnl = 0.0

        elif side == "BUY" and old_side == "SHORT":
            closed_qty = min(quantity, old_qty)
            existing.realized_pnl += (old_avg - price) * closed_qty * DEFAULT_CONTRACT_SIZE
            existing.total_costs += fill_cost
            remaining = quantity - old_qty
            if remaining > 0:
                existing.side = "LONG"
                existing.quantity = remaining
                existing.average_price = price
                existing.notional = remaining * price * DEFAULT_CONTRACT_SIZE
                existing.unrealized_pnl = 0.0
            else:
                existing.quantity = old_qty - quantity
                if existing.quantity > 0:
                    existing.notional = existing.quantity * old_avg * DEFAULT_CONTRACT_SIZE
                else:
                    existing.side = "FLAT"
                    existing.quantity = 0.0
                    existing.average_price = 0.0
                    existing.notional = 0.0
                    existing.unrealized_pnl = 0.0

        elif side == "FLATTEN":
            if old_side == "LONG":
                existing.realized_pnl += (price - old_avg) * old_qty * DEFAULT_CONTRACT_SIZE
            elif old_side == "SHORT":
                existing.realized_pnl += (old_avg - price) * old_qty * DEFAULT_CONTRACT_SIZE
            existing.total_costs += fill_cost
            existing.side = "FLAT"
            existing.quantity = 0.0
            existing.average_price = 0.0
            existing.notional = 0.0
            existing.unrealized_pnl = 0.0

        else:
            raise ValueError(f"Unsupported fill side {side!r} for position side {old_side!r}")

        existing.updated_at = now
        return existing

    def mark_to_market(self, symbol: str, timeframe: str, latest_price: float) -> Optional[Position]:
        """Update gross unrealized PnL using latest close."""
        pos = self.positions.get(self._key(symbol, timeframe))
        if pos is None or pos.side == "FLAT" or pos.quantity == 0:
            if pos is not None:
                pos.unrealized_pnl = 0.0
            return pos
        if pos.side == "LONG":
            pos.unrealized_pnl = (
                (latest_price - pos.average_price) * pos.quantity * DEFAULT_CONTRACT_SIZE
            )
        elif pos.side == "SHORT":
            pos.unrealized_pnl = (
                (pos.average_price - latest_price) * pos.quantity * DEFAULT_CONTRACT_SIZE
            )
        pos.updated_at = datetime.now(timezone.utc).isoformat()
        return pos

    def all_positions(self) -> List[Position]:
        return list(self.positions.values())

    def flatten_all(self, price: float) -> List[Position]:
        """Flatten all positions at given price."""
        updated = []
        for pos in list(self.positions.values()):
            if pos.side != "FLAT" and pos.quantity > 0:
                self.update_position(
                    symbol=pos.symbol,
                    timeframe=pos.timeframe,
                    side="FLATTEN",
                    quantity=pos.quantity,
                    price=price,
                    fill_cost=0.0,
                )
                updated.append(pos)
        return updated
