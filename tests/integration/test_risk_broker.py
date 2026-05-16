
import os
import pytest
from core.risk import RiskManager
from core.paper_broker import PaperBroker

def test_risk_then_broker():
    rm = RiskManager(max_exposure=5.0)
    broker = PaperBroker(balance=100000)
    decision = rm.evaluate("EURUSD", "buy", 3.0)
    assert decision.allowed is True
    oid, pid = broker.open_position("EURUSD", "buy", 3.0, 1.1000)
    assert broker.positions[pid].volume == 3.0
