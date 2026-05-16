
import pytest
from backtesting.walk_forward import WalkForward
from research.example_strategies import DummyAlwaysBuy

def test_folds_do_not_overlap():
    data = [
        {"timestamp": f"2024-01-{i:02d}T00:00:00", "symbol": "EURUSD", "bid": 1.1, "ask": 1.1002}
        for i in range(1, 21)
    ]
    wf = WalkForward(data, DummyAlwaysBuy, n_folds=4)
    results = wf.run()
    assert len(results) == 4
    for i, r in enumerate(results):
        assert r["fold"] == i + 1
