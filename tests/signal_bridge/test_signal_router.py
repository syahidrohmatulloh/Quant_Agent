
import pytest
from signal_bridge.signal_router import SignalRouter

def test_paper_only_routes_to_paper():
    router = SignalRouter(paper_only=True)
    signal = {"generated": True, "signal": "buy"}
    result = router.route(signal)
    assert result["routed"] is True
    assert result["destination"] == "paper"

def test_ungenerated_signal_not_routed():
    router = SignalRouter()
    signal = {"generated": False}
    result = router.route(signal)
    assert result["routed"] is False
