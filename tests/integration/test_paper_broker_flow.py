
import os
import pytest
from core.paper_broker import PaperBroker

def test_multiple_positions():
    broker = PaperBroker(balance=100000)
    o1, p1 = broker.open_position("EURUSD", "buy", 1.0, 1.1000)
    o2, p2 = broker.open_position("GBPUSD", "sell", 2.0, 1.2500)
    assert len(broker.positions) == 2
    broker.close_position(p1, 1.1010)
    assert broker.positions[p1].status == "closed"
    assert broker.positions[p2].status == "open"
