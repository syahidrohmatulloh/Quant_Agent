"""OANDA practice positions parser."""
from typing import Dict, Any, List


def parse_positions(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    positions = []
    for p in raw.get("positions", []):
        positions.append({
            "symbol": p.get("instrument", ""),
            "long_units": float(p.get("long", {}).get("units", 0)),
            "short_units": float(p.get("short", {}).get("units", 0)),
            "avg_long_price": float(p.get("long", {}).get("averagePrice", 0)),
            "avg_short_price": float(p.get("short", {}).get("averagePrice", 0)),
        })
    return positions
