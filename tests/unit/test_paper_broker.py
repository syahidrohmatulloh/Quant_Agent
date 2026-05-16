
import os
import pytest
from core.paper_broker import PaperBroker

def test_long_open_at_ask():
    broker = PaperBroker(balance=100000)
    oid, pid = broker.open_position("EURUSD", "buy", 1.0, 1.10025, sl=1.08, tp=1.12)
    assert oid.startswith("PAPER-ORDER")
    assert pid.startswith("PAPER-POS")
    pos = broker.positions[pid]
    assert pos.direction == "buy"
    assert pos.entry_price == 1.10025

def test_close_position_pnl():
    broker = PaperBroker(balance=100000)
    oid, pid = broker.open_position("EURUSD", "buy", 1.0, 1.10000)
    broker.close_position(pid, 1.10100)
    assert broker.positions[pid].status == "closed"
    assert broker.positions[pid].realized_pnl > 0

def test_update_prices():
    broker = PaperBroker(balance=100000)
    oid, pid = broker.open_position("EURUSD", "buy", 1.0, 1.10000)
    broker.update_prices("EURUSD", 1.09900, 1.09950)
    assert broker.positions[pid].current_price == 1.09950

def test_short_position():
    broker = PaperBroker(balance=100000)
    oid, pid = broker.open_position("EURUSD", "sell", 1.0, 1.10000)
    broker.close_position(pid, 1.09900)
    assert broker.positions[pid].realized_pnl > 0

def test_balance_updates():
    broker = PaperBroker(balance=100000)
    oid, pid = broker.open_position("EURUSD", "buy", 1.0, 1.10000)
    initial = broker.balance
    broker.close_position(pid, 1.10100)
    assert broker.balance != initial

def test_order_counter_increments():
    broker = PaperBroker(balance=100000)
    o1, p1 = broker.open_position("EURUSD", "buy", 1.0, 1.1)
    o2, p2 = broker.open_position("EURUSD", "buy", 1.0, 1.1)
    assert int(o2.split("-")[-1]) == int(o1.split("-")[-1]) + 1
