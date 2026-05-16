
import pytest
from monitoring.live_metrics import LiveMetrics

def test_record_signal():
    m = LiveMetrics()
    m.record_signal(True)
    assert m.signals_generated == 1
    m.record_signal(False, "risk")
    assert m.signals_rejected == 1
    assert m.rejected_by_reason["risk"] == 1

def test_record_order():
    m = LiveMetrics()
    m.record_order()
    assert m.orders_created == 1

def test_record_pnl():
    m = LiveMetrics()
    m.record_pnl(100)
    m.record_pnl(-50)
    assert m.wins == 1
    assert m.losses == 1

def test_summary():
    m = LiveMetrics()
    m.record_signal(True)
    m.record_signal(False, "risk")
    m.record_order()
    m.record_pnl(100)
    s = m.summary()
    assert s["signals_generated"] == 1
    assert s["signals_rejected"] == 1
    assert s["win_rate"] == 1.0
