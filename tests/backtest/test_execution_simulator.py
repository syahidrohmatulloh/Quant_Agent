
import pytest
from datetime import datetime
from backtesting.execution_simulator import ExecutionSimulator
from backtesting.event import OrderEvent, MarketEvent

def test_long_open_at_ask():
    sim = ExecutionSimulator(commission_per_lot=7.0, slippage_pips=0.5)
    market = MarketEvent(datetime(2024, 1, 1), "EURUSD", 1.1000, 1.1002)
    order = OrderEvent(datetime(2024, 1, 1), "EURUSD", "buy", 1.0)
    fill = sim.simulate_fill(order, market)
    assert fill.fill_price >= market.ask
    assert fill.commission == 7.0

def test_short_open_at_bid():
    sim = ExecutionSimulator(commission_per_lot=7.0, slippage_pips=0.5)
    market = MarketEvent(datetime(2024, 1, 1), "EURUSD", 1.1000, 1.1002)
    order = OrderEvent(datetime(2024, 1, 1), "EURUSD", "sell", 1.0)
    fill = sim.simulate_fill(order, market)
    assert fill.fill_price <= market.bid
