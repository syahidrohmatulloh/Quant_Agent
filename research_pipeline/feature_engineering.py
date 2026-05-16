
import numpy as np
import pandas as pd
from typing import Dict, Any

def compute_returns(df: pd.DataFrame, col: str = "close") -> pd.Series:
    return df[col].pct_change()

def compute_log_returns(df: pd.DataFrame, col: str = "close") -> pd.Series:
    return np.log(df[col] / df[col].shift(1))

def compute_rolling_volatility(df: pd.DataFrame, window: int = 20, col: str = "close") -> pd.Series:
    return df[col].pct_change().rolling(window=window).std()

def compute_moving_average(df: pd.DataFrame, window: int = 20, col: str = "close") -> pd.Series:
    return df[col].rolling(window=window).mean()

def compute_rsi(df: pd.DataFrame, window: int = 14, col: str = "close") -> pd.Series:
    delta = df[col].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_spread(df: pd.DataFrame) -> pd.Series:
    if "ask" in df.columns and "bid" in df.columns:
        return df["ask"] - df["bid"]
    return pd.Series(np.nan, index=df.index)

def compute_volume_change(df: pd.DataFrame, col: str = "volume") -> pd.Series:
    if col not in df.columns:
        return pd.Series(np.nan, index=df.index)
    return df[col].pct_change()

def compute_time_features(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    ts = pd.to_datetime(df[timestamp_col]) if timestamp_col in df.columns else pd.to_datetime(df.index)
    features = pd.DataFrame(index=df.index)
    features["hour"] = ts.dt.hour
    features["day_of_week"] = ts.dt.dayofweek
    features["month"] = ts.dt.month
    return features

class FeatureEngineer:
    def __init__(self):
        self.features: Dict[str, pd.Series] = {}

    def add(self, name: str, series: pd.Series):
        self.features[name] = series

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.features)
