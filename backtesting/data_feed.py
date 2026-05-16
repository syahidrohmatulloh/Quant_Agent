
import json
from datetime import datetime
from typing import List, Dict, Any, Iterator
from backtesting.event import MarketEvent

class HistoricalDataFeed:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self._validate()

    def _validate(self):
        for row in self.data:
            assert "timestamp" in row, "Missing timestamp"
            assert "symbol" in row, "Missing symbol"
            assert "bid" in row, "Missing bid"
            assert "ask" in row, "Missing ask"
            assert row["ask"] >= row["bid"], "Ask < bid"

    def __iter__(self) -> Iterator[MarketEvent]:
        for row in self.data:
            ts = row["timestamp"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            yield MarketEvent(
                timestamp=ts,
                symbol=row["symbol"],
                bid=float(row["bid"]),
                ask=float(row["ask"]),
                extra=row.get("extra", {})
            )

    @classmethod
    def from_json_file(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)
