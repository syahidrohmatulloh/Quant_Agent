
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LabelConfig:
    method: str  # next_return, direction, triple_barrier
    horizon: int
    upper_barrier: Optional[float] = None
    lower_barrier: Optional[float] = None

def build_next_return(df: pd.DataFrame, horizon: int = 1, col: str = "close") -> pd.Series:
    return df[col].shift(-horizon) / df[col] - 1

def build_direction(df: pd.DataFrame, horizon: int = 1, col: str = "close") -> pd.Series:
    future = df[col].shift(-horizon)
    return pd.Series(np.where(future > df[col], 1, np.where(future < df[col], -1, 0)), index=df.index)

def build_triple_barrier(df: pd.DataFrame, horizon: int, upper: float, lower: float,
                         col: str = "close") -> pd.Series:
    labels = []
    for i in range(len(df)):
        if i + horizon >= len(df):
            labels.append(np.nan)
            continue
        start_price = df[col].iloc[i]
        window = df[col].iloc[i+1:i+horizon+1]
        if (window >= start_price * (1 + upper)).any():
            labels.append(1)
        elif (window <= start_price * (1 - lower)).any():
            labels.append(-1)
        else:
            labels.append(0)
    return pd.Series(labels, index=df.index)

class LabelBuilder:
    def __init__(self, config: LabelConfig):
        self.config = config
        self.labels: Optional[pd.Series] = None
        self.metadata: Dict[str, Any] = {}

    def build(self, df: pd.DataFrame, col: str = "close") -> pd.Series:
        cfg = self.config
        if cfg.method == "next_return":
            self.labels = build_next_return(df, cfg.horizon, col)
        elif cfg.method == "direction":
            self.labels = build_direction(df, cfg.horizon, col)
        elif cfg.method == "triple_barrier":
            self.labels = build_triple_barrier(df, cfg.horizon, cfg.upper_barrier, cfg.lower_barrier, col)
        else:
            raise ValueError(f"Unknown label method: {cfg.method}")
        # Drop rows where future is unavailable (lookahead leakage prevention)
        self.labels = self.labels.iloc[:-cfg.horizon]
        self.metadata = {
            "method": cfg.method,
            "horizon": cfg.horizon,
            "upper_barrier": cfg.upper_barrier,
            "lower_barrier": cfg.lower_barrier,
            "label_count": int(self.labels.notna().sum()),
            "dropped_rows": cfg.horizon
        }
        return self.labels

    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata
