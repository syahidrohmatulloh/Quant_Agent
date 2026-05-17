import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import pytest
from broker_integration.mt5.mt5_config import get_mt5_timeframe, get_string_timeframe, TIMEFRAME_MAP


def test_get_mt5_timeframe_valid():
    assert get_mt5_timeframe("M1") == 1
    assert get_mt5_timeframe("H1") == 60
    assert get_mt5_timeframe("D1") == 1440


def test_get_mt5_timeframe_invalid():
    with pytest.raises(ValueError):
        get_mt5_timeframe("INVALID")


def test_get_string_timeframe_valid():
    assert get_string_timeframe(1) == "M1"
    assert get_string_timeframe(60) == "H1"
    assert get_string_timeframe(1440) == "D1"


def test_get_string_timeframe_invalid():
    with pytest.raises(ValueError):
        get_string_timeframe(999)


def test_all_timeframes_mapped():
    assert set(TIMEFRAME_MAP.keys()) == {"M1", "M5", "M15", "M30", "H1", "H4", "D1"}
