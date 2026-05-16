
import pytest
from backtesting.execution_simulator import ExecutionSimulator
from backtesting.event import OrderEvent, MarketEvent
from datetime import datetime

def test_commission_calculation():
    sim = ExecutionSimulator(commission_per_lot=10.0)
    market = MarketEvent(datetime(2024, 1, 1), "EURUSD", 1.1, 1.1002)
    order = OrderEvent(datetime(2024, 1, 1), "EURUSD", "buy", 2.0)
    fill = sim.simulate_fill(order, market)
    assert fill.commission == 20.0

def test_slippage_applied():
    sim = ExecutionSimulator(slippage_pips=1.0)
    market = MarketEvent(datetime(2024, 1, 1), "EURUSD", 1.1000, 1.1002)
    order = OrderEvent(datetime(2024, 1, 1), "EURUSD", "buy", 1.0)
    fill = sim.simulate_fill(order, market)
    assert fill.fill_price > market.ask
