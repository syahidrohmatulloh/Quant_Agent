
import os
import pytest
from core.risk import RiskManager

def test_risk_allows_small_volume():
    rm = RiskManager(max_exposure=10.0)
    decision = rm.evaluate("EURUSD", "buy", 1.0)
    assert decision.allowed is True
    assert decision.severity == "low"

def test_risk_blocks_large_volume():
    rm = RiskManager(max_exposure=5.0)
    decision = rm.evaluate("EURUSD", "buy", 10.0)
    assert decision.allowed is False
    assert decision.severity == "high"

def test_risk_exact_boundary():
    rm = RiskManager(max_exposure=5.0)
    decision = rm.evaluate("EURUSD", "buy", 5.0)
    assert decision.allowed is True

def test_risk_decision_id_present():
    rm = RiskManager()
    decision = rm.evaluate("EURUSD", "buy", 1.0)
    assert decision.risk_decision_id
    assert decision.checks is not None
