
import pytest
from backtesting.portfolio_simulator import PortfolioSimulator
from backtesting.event import FillEvent, PositionClosedEvent
from datetime import datetime

def test_portfolio_initial_balance():
    p = PortfolioSimulator(100000)
    assert p.cash == 100000
    assert p.equity == 100000

def test_on_fill_reduces_cash():
    p = PortfolioSimulator(100000)
    fill = FillEvent(datetime(2024,1,1), "EURUSD", "buy", 1.0, 1.1000, 7.0)
    p.on_fill(fill)
    assert p.cash < 100000

def test_on_position_closed_updates_trades():
    p = PortfolioSimulator(100000)
    closed = PositionClosedEvent(datetime(2024,1,1), "EURUSD", "buy", 1.0, 1.1000, 1.1010, 100, 7.0)
    p.on_position_closed(closed)
    assert len(p.trades) == 1
    assert p.trades[0]["pnl"] == 100
