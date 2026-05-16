
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pandas as pd

class DatasetBuilder:
    def __init__(self):
        self.datasets: Dict[str, Dict[str, Any]] = {}

    def build(self, data: List[Dict[str, Any]], source: str = "ohlcv",
              symbols: Optional[List[str]] = None,
              timeframe: str = "1m") -> Dict[str, Any]:
        df = pd.DataFrame(data)
        self._validate(df)
        dataset_id = str(uuid.uuid4())
        start_time = df["timestamp"].min() if "timestamp" in df.columns else None
        end_time = df["timestamp"].max() if "timestamp" in df.columns else None
        row_count = len(df)
        data_hash = self._hash(df)
        meta = {
            "dataset_id": dataset_id,
            "source": source,
            "symbols": symbols or [df["symbol"].unique().tolist()] if "symbol" in df.columns else [],
            "timeframe": timeframe,
            "start_time": str(start_time),
            "end_time": str(end_time),
            "row_count": row_count,
            "data_hash": data_hash,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.datasets[dataset_id] = {"meta": meta, "data": df}
        return meta

    def _validate(self, df: pd.DataFrame):
        if df.empty:
            raise ValueError("Dataset is empty")
        if "timestamp" in df.columns:
            dups = df["timestamp"].duplicated().sum()
            if dups > 0:
                raise ValueError(f"Duplicate timestamps found: {dups}")
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                invalid = ((df[col] <= 0) | (df[col].isna())).sum()
                if invalid > 0:
                    raise ValueError(f"Invalid OHLC in column {col}: {invalid} rows")
        if all(c in df.columns for c in ["high", "low", "close"]):
            if not ((df["high"] >= df["low"]) & (df["high"] >= df["close"]) & (df["low"] <= df["close"])).all():
                raise ValueError("Invalid OHLC relationship: high < low or high < close or low > close")

    def _hash(self, df: pd.DataFrame) -> str:
        return hashlib.sha256(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()[:16]

    def get(self, dataset_id: str) -> Optional[pd.DataFrame]:
        entry = self.datasets.get(dataset_id)
        return entry["data"] if entry else None

    def get_meta(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        entry = self.datasets.get(dataset_id)
        return entry["meta"] if entry else None
