"""
Test consensus engine and signal normalization.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from experiment_manager.strategy_comparison import normalize_signal
from experiment_manager.consensus import compute_consensus


def test_signal_normalize_long():
    assert normalize_signal("long") == "LONG"
    assert normalize_signal("buy") == "LONG"
    assert normalize_signal("bullish") == "LONG"
    assert normalize_signal(1) == "LONG"
    assert normalize_signal("1") == "LONG"


def test_signal_normalize_short():
    assert normalize_signal("short") == "SHORT"
    assert normalize_signal("sell") == "SHORT"
    assert normalize_signal("bearish") == "SHORT"
    assert normalize_signal(-1) == "SHORT"
    assert normalize_signal("-1") == "SHORT"


def test_signal_normalize_neutral():
    assert normalize_signal("neutral") == "NEUTRAL"
    assert normalize_signal("hold") == "NEUTRAL"
    assert normalize_signal("flat") == "NEUTRAL"
    assert normalize_signal(0) == "NEUTRAL"
    assert normalize_signal("0") == "NEUTRAL"
    assert normalize_signal(None) == "NEUTRAL"


def test_signal_normalize_unknown():
    assert normalize_signal("random") == "UNKNOWN"
    assert normalize_signal(99) == "UNKNOWN"


def test_majority_vote_consensus():
    rows = [
        {"signal": "LONG"},
        {"signal": "LONG"},
        {"signal": "SHORT"},
    ]
    result = compute_consensus(rows, method="majority_vote", minimum_agreement=0.6)
    assert result["consensus_signal"] == "LONG"
    assert result["agreement_ratio"] == pytest.approx(2/3, abs=0.01)
    assert result["confidence_label"] == "medium"


def test_weighted_vote_consensus():
    rows = [
        {"signal": "LONG", "weight": 0.8},
        {"signal": "SHORT", "weight": 0.2},
    ]
    result = compute_consensus(rows, method="weighted_vote", minimum_agreement=0.6)
    assert result["consensus_signal"] == "LONG"
    assert result["agreement_ratio"] == pytest.approx(0.6, abs=0.01)


def test_conservative_avoids_conflict():
    rows = [
        {"signal": "LONG"},
        {"signal": "SHORT"},
    ]
    result = compute_consensus(rows, method="conservative", minimum_agreement=0.6)
    assert result["consensus_signal"] == "NEUTRAL"
    assert result["conflict_detected"] is True
    assert "conflict" in result["explanation"].lower()


def test_unanimous_only_requires_full_agreement():
    rows = [
        {"signal": "LONG"},
        {"signal": "LONG"},
    ]
    result = compute_consensus(rows, method="unanimous_only")
    assert result["consensus_signal"] == "LONG"
    assert result["agreement_ratio"] == 1.0

    rows2 = [
        {"signal": "LONG"},
        {"signal": "NEUTRAL"},
    ]
    result2 = compute_consensus(rows2, method="unanimous_only")
    assert result2["consensus_signal"] == "NEUTRAL"


def test_conflict_detection():
    rows = [
        {"signal": "LONG"},
        {"signal": "SHORT"},
        {"signal": "NEUTRAL"},
    ]
    result = compute_consensus(rows, method="majority_vote")
    assert result["conflict_detected"] is True
