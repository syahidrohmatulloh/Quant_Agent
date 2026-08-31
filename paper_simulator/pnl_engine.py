"""PnL engine for paper simulation.

Mark-to-market using latest close from CSV. Explicitly label as simulated.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List

from paper_simulator.position_book import PositionBook, DEFAULT_CONTRACT_SIZE


class PnlSnapshot:
    """Snapshot of portfolio PnL."""

    def __init__(
        self,
        timestamp: str,
        realized_pnl: float,
        unrealized_pnl: float,
        total_pnl: float,
        total_costs: float,
        equity: float,
        cash_simulated: float,
        gross_exposure: float,
        net_exposure: float,
        per_symbol_pnl: Dict[str, float],
        warnings: List[str],
    ):
        self.timestamp = timestamp
        self.realized_pnl = realized_pnl
        self.unrealized_pnl = unrealized_pnl
        self.total_pnl = total_pnl
        self.total_costs = total_costs
        self.equity = equity
        self.cash_simulated = cash_simulated
        self.gross_exposure = gross_exposure
        self.net_exposure = net_exposure
        self.per_symbol_pnl = per_symbol_pnl
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "total_pnl": self.total_pnl,
            "total_costs": self.total_costs,
            "equity": self.equity,
            "cash_simulated": self.cash_simulated,
            "gross_exposure": self.gross_exposure,
            "net_exposure": self.net_exposure,
            "per_symbol_pnl": self.per_symbol_pnl,
            "warnings": self.warnings,
            "simulated": True,
            "paper_only": True,
            "data_only": True,
        }


def compute_pnl(
    position_book: PositionBook,
    latest_prices: Dict[str, float],
    initial_cash: float,
    base_currency: str,
) -> PnlSnapshot:
    """Compute portfolio PnL with transaction costs accounted exactly once."""
    warnings: List[str] = []
    realized = 0.0
    unrealized = 0.0
    total_costs = 0.0
    gross_exposure = 0.0
    net_exposure = 0.0
    per_symbol: Dict[str, float] = {}

    for pos in position_book.all_positions():
        key = pos.symbol + "_" + pos.timeframe
        price = latest_prices.get(pos.symbol)

        if pos.side != "FLAT" and pos.quantity > 0:
            if price is None:
                warnings.append("No price data for " + pos.symbol + "; skipping mark-to-market.")
            else:
                position_book.mark_to_market(pos.symbol, pos.timeframe, price)
                notional = abs(pos.quantity) * price * DEFAULT_CONTRACT_SIZE
                gross_exposure += notional
                if pos.side == "LONG":
                    net_exposure += notional
                elif pos.side == "SHORT":
                    net_exposure -= notional
        else:
            pos.unrealized_pnl = 0.0

        realized += pos.realized_pnl
        unrealized += pos.unrealized_pnl
        total_costs += pos.total_costs
        per_symbol[key] = pos.realized_pnl + pos.unrealized_pnl - pos.total_costs

    total_pnl = realized + unrealized - total_costs
    equity = initial_cash + total_pnl
    cash = initial_cash + realized - total_costs - gross_exposure

    return PnlSnapshot(
        timestamp=datetime.now(timezone.utc).isoformat(),
        realized_pnl=round(realized, 4),
        unrealized_pnl=round(unrealized, 4),
        total_pnl=round(total_pnl, 4),
        total_costs=round(total_costs, 4),
        equity=round(equity, 2),
        cash_simulated=round(cash, 2),
        gross_exposure=round(gross_exposure, 2),
        net_exposure=round(net_exposure, 2),
        per_symbol_pnl={k: round(v, 4) for k, v in per_symbol.items()},
        warnings=warnings,
    )
