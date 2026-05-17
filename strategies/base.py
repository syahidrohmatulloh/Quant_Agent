"""
Base definitions for evidence-based institutional-style quant strategy families.
All outputs are signals / weights / paper-only recommendations.
No live trading. No profitability guarantees.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass(frozen=True)
class StrategySignal:
    timestamp: datetime
    symbol: str
    signal: str  # e.g., 'buy', 'sell', 'hold', 'long', 'short', 'flat'
    weight: float = 0.0  # normalized position weight [-1, 1]
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyResult:
    signals: List[StrategySignal] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    disclaimer: str = "PAPER-ONLY / EDUCATIONAL. Past performance does not guarantee future results."


@dataclass
class StrategyConfig:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    symbols: List[str] = field(default_factory=list)
    timeframe: str = "D1"
    paper_only: bool = True

    def validate(self) -> None:
        if not self.name:
            raise ValueError("Strategy name is required.")
        if not self.symbols:
            raise ValueError("At least one symbol is required.")
        if self.timeframe not in ("M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"):
            raise ValueError(f"Unsupported timeframe: {self.timeframe}")


class BaseStrategy(ABC):
    """Abstract base for all strategy families."""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.config.validate()

    @abstractmethod
    def generate(self, data: Dict[str, List[Dict[str, Any]]]) -> StrategyResult:
        """
        data: mapping symbol -> list of bar dicts with keys:
              'timestamp', 'open', 'high', 'low', 'close', 'volume'
        Returns StrategyResult with signals and optional metadata.
        """
        ...

    def _disclaimer(self) -> str:
        return (
            "This is an evidence-based institutional-style quant strategy family "
            "for research and educational purposes only. It is paper-only, "
            "not guaranteed profitable, and not a proprietary hedge fund strategy."
        )
