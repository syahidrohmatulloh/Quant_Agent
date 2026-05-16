
from typing import Dict, Any
from datetime import datetime, timezone, timedelta

class MarketClock:
    """FX market clock. Assumes UTC."""
    def __init__(self):
        self.fx_open_hour = 22  # Sunday 22:00 UTC
        self.fx_close_hour = 22  # Friday 22:00 UTC

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def is_weekend(self, dt: datetime = None) -> bool:
        dt = dt or self.now()
        wd = dt.weekday()
        if wd == 5:  # Saturday
            return True
        if wd == 4 and dt.hour >= self.fx_close_hour:  # Friday after 22:00
            return True
        if wd == 6 and dt.hour < self.fx_open_hour:  # Sunday before 22:00
            return True
        return False

    def is_trading_window(self, dt: datetime = None) -> bool:
        return not self.is_weekend(dt)

    def session_status(self) -> Dict[str, Any]:
        now = self.now()
        return {
            "timestamp_utc": now.isoformat(),
            "is_weekend": self.is_weekend(now),
            "is_trading": self.is_trading_window(now),
            "next_open": self._next_open(now).isoformat() if self.is_weekend(now) else now.isoformat()
        }

    def _next_open(self, dt: datetime) -> datetime:
        # Simple: next Sunday 22:00 UTC
        days_until_sunday = (6 - dt.weekday()) % 7
        if days_until_sunday == 0 and dt.hour >= self.fx_open_hour:
            days_until_sunday = 7
        next_sun = dt.date() + timedelta(days=days_until_sunday)
        return datetime(next_sun.year, next_sun.month, next_sun.day, self.fx_open_hour, 0, tzinfo=timezone.utc)
