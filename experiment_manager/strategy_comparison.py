"""
Strategy comparison table builder and signal normalization.
Paper-only. No live trading.
"""
from typing import Dict, Any, List, Optional

SIGNAL_MAP = {
    "long": "LONG", "buy": "LONG", "bullish": "LONG", "1": "LONG", 1: "LONG",
    "short": "SHORT", "sell": "SHORT", "bearish": "SHORT", "-1": "SHORT", -1: "SHORT",
    "neutral": "NEUTRAL", "hold": "NEUTRAL", "flat": "NEUTRAL", "0": "NEUTRAL", 0: "NEUTRAL",
}


def normalize_signal(raw):
    if raw is None:
        return "NEUTRAL"
    if isinstance(raw, str):
        key = raw.lower().strip()
    else:
        key = raw
    return SIGNAL_MAP.get(key, "UNKNOWN")


def build_comparison_table(strategy_results, backtest_results=None):
    bt_map = {}
    if backtest_results:
        for bt in backtest_results:
            if bt and bt.get("status") == "ok":
                bt_map[bt.get("strategy")] = bt.get("backtest", {})

    rows = []
    for r in strategy_results:
        if not r or r.get("status") != "ok":
            continue
        strat_name = r.get("strategy", "unknown")
        latest = r.get("latest_signal", {})
        raw_sig = latest.get("direction") if latest else None
        norm_sig = normalize_signal(raw_sig)
        metrics = r.get("metrics", {})
        bt = bt_map.get(strat_name, {})

        row = {
            "strategy": strat_name,
            "signal": norm_sig,
            "score": latest.get("score") if latest else None,
            "weight": latest.get("weight") if latest else None,
            "confidence": latest.get("confidence") if latest else None,
            "backtest_return": bt.get("total_return"),
            "max_drawdown": bt.get("max_drawdown"),
            "warnings": [],
        }
        if norm_sig == "UNKNOWN":
            row["warnings"].append("Unrecognized signal direction: " + str(raw_sig))
        rows.append(row)
    return rows
