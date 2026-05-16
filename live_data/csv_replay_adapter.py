
import json
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
from live_data.base_adapter import BaseMarketDataAdapter
from live_data.data_normalizer import DataNormalizer

class CSVReplayAdapter(BaseMarketDataAdapter):
    def __init__(self, source_path: str, speed_multiplier: float = 1.0,
                 tick_mode: bool = True, source: str = "csv_replay"):
        self.source_path = source_path
        self.speed_multiplier = speed_multiplier
        self.tick_mode = tick_mode
        self.source = source
        self._data: List[Dict[str, Any]] = []
        self._index = 0
        self._connected = False
        self._paused = False

    def connect(self) -> bool:
        self._load()
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def is_connected(self) -> bool:
        return self._connected

    def _load(self):
        if self.source_path.endswith(".json"):
            with open(self.source_path, "r") as f:
                self._data = json.load(f)
        elif self.source_path.endswith(".csv"):
            with open(self.source_path, "r") as f:
                reader = csv.DictReader(f)
                self._data = list(reader)
        else:
            raise ValueError("Unsupported file format")

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self._connected or self._index >= len(self._data):
            return None
        raw = self._data[self._index]
        self._index += 1
        if self.tick_mode:
            return DataNormalizer.normalize_tick(raw, self.source)
        return DataNormalizer.normalize_tick(raw, self.source)

    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int) -> List[Dict[str, Any]]:
        if not self._connected:
            return []
        start = max(0, self._index - lookback)
        end = self._index
        bars = []
        for row in self._data[start:end]:
            bar = DataNormalizer.normalize_bar(row, self.source)
            if bar:
                bars.append(bar)
        return bars

    def health_check(self) -> Dict[str, Any]:
        return {
            "connected": self._connected,
            "total_rows": len(self._data),
            "current_index": self._index,
            "finished": self._index >= len(self._data),
            "paused": self._paused
        }

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def reset(self):
        self._index = 0
