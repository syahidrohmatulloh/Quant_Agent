
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class BaseMarketDataAdapter(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        pass
