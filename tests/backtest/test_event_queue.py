
import pytest
from datetime import datetime
from backtesting.event_queue import EventQueue
from backtesting.event import MarketEvent

def test_processes_in_timestamp_order():
    q = EventQueue()
    t1 = datetime(2024, 1, 1, 10, 0)
    t2 = datetime(2024, 1, 1, 9, 0)
    t3 = datetime(2024, 1, 1, 11, 0)
    q.put(t1, "a")
    q.put(t2, "b")
    q.put(t3, "c")
    assert q.get()[1] == "b"
    assert q.get()[1] == "a"
    assert q.get()[1] == "c"
    assert q.empty()
