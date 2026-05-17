"""
Test append-only signal log.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import tempfile
import json
from pathlib import Path
from strategy_runtime.signal_log import log_signal, read_signals


def test_log_signal_append():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "signals.jsonl")
        sig = {
            "symbol": "EURUSD",
            "timeframe": "H1",
            "strategy": "ma_crossover",
            "direction": "long",
            "weight": 0.5,
            "source_csv": "/tmp/test.csv",
        }
        log_signal(sig, log_path=log_path)
        log_signal(sig, log_path=log_path)
        signals = read_signals(log_path)
        assert len(signals) == 2
        assert signals[0]["paper_only"] is True
        assert signals[0]["data_only"] is True
        assert signals[0]["no_order_submission"] is True
        assert signals[0]["symbol"] == "EURUSD"


def test_read_empty_log():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "empty.jsonl")
        assert read_signals(log_path) == []
