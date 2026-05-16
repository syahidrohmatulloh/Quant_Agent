"""Market data stream abstraction."""
from typing import Dict, Any, Optional, Iterator
from abc import ABC, abstractmethod


class MarketDataStream(ABC):
    """Abstract market data stream."""

    @abstractmethod
    def start(self, symbol: str = "EURUSD") -> Iterator[Dict[str, Any]]:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        pass
