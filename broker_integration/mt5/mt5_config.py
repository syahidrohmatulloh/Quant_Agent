"""
MT5 configuration and timeframe mapping.
No credentials. No account info. No live trading config.
"""
from typing import Dict, Any

# Mapping from our string timeframes to MT5 integer constants
TIMEFRAME_MAP: Dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

# Reverse mapping
TIMEFRAME_REVERSE: Dict[int, str] = {v: k for k, v in TIMEFRAME_MAP.items()}


def get_mt5_timeframe(tf: str) -> int:
    if tf not in TIMEFRAME_MAP:
        raise ValueError(f"Unsupported timeframe: {tf}. Supported: {list(TIMEFRAME_MAP.keys())}")
    return TIMEFRAME_MAP[tf]


def get_string_timeframe(mt5_tf: int) -> str:
    if mt5_tf not in TIMEFRAME_REVERSE:
        raise ValueError(f"Unknown MT5 timeframe constant: {mt5_tf}")
    return TIMEFRAME_REVERSE[mt5_tf]


class MT5Config:
    """Minimal MT5 connection config. No credentials."""

    def __init__(self, timeout: int = 60000, portable: bool = False):
        self.timeout = timeout
        self.portable = portable

    def to_dict(self) -> Dict[str, Any]:
        return {"timeout": self.timeout, "portable": self.portable}
