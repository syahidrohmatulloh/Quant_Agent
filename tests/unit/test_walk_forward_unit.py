
import pytest
from backtesting.walk_forward import WalkForward
from research.example_strategies import DummyAlwaysBuy

def test_walk_forward_splits():
    data = [
        {"timestamp": f"2024-01-{i:02d}T00:00:00", "symbol": "EURUSD", "bid": 1.1, "ask": 1.1002}
        for i in range(1, 11)
    ]
    wf = WalkForward(data, DummyAlwaysBuy, n_folds=2)
    results = wf.run()
    assert len(results) == 2
    assert results[0]["test_size"] == 5
    assert results[1]["test_size"] == 5
