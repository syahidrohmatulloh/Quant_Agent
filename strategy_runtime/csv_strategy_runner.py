"""
Run Phase 10 strategies on normalized CSV market data.
Paper-only. No live trading. No broker calls.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path

from market_data.csv_loader import load_csv_strategy_shape
from market_data.csv_validator import validate_csv
from strategies.registry import StrategyRegistry
from strategies.base import StrategyConfig, StrategyResult
from strategy_lab.backtest import SimpleBacktestEngine


def run_strategy_on_csv(
    csv_path: str,
    strategy_name: str,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    strategy_params: Optional[Dict[str, Any]] = None,
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Load CSV, optionally validate, run strategy, return result.
    Always prints paper-only disclaimer.
    """
    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    if validate:
        v = validate_csv(csv_path, symbol=symbol, timeframe=timeframe)
        if not v["valid"]:
            return {
                "status": "validation_failed",
                "validation": v,
                "signals": [],
                "disclaimer": "PAPER-ONLY / DATA-ONLY. No live trading.",
            }

    data = load_csv_strategy_shape(csv_path, symbol=symbol, timeframe=timeframe)
    sym = symbol or list(data.keys())[0]

    strat_class = StrategyRegistry.get(strategy_name)
    cfg = StrategyConfig(
        name=strategy_name,
        symbols=[sym],
        timeframe=timeframe or "H1",
        params=strategy_params or {},
    )
    strategy = strat_class(cfg)
    result = strategy.generate(data)

    latest_signal = None
    if result.signals:
        latest = result.signals[-1]
        latest_signal = {
            "timestamp": latest.timestamp.isoformat() if hasattr(latest.timestamp, "isoformat") else str(latest.timestamp),
            "symbol": latest.symbol,
            "direction": latest.signal,
            "weight": latest.weight,
            "score": latest.meta.get("score") if latest.meta else None,
            "confidence": latest.meta.get("confidence") if latest.meta else None,
            "strategy": strategy_name,
            "source_csv": str(Path(csv_path).resolve()),
        }

    return {
        "status": "ok",
        "symbol": sym,
        "timeframe": timeframe or "UNKNOWN",
        "strategy": strategy_name,
        "latest_signal": latest_signal,
        "signal_count": len(result.signals),
        "metrics": result.metrics,
        "disclaimer": result.disclaimer,
    }


def run_backtest_on_csv(
    csv_path: str,
    strategy_name: str,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    initial_balance: float = 100000.0,
    strategy_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run historical simulation (backtest) on CSV data.
    Paper-only. No profitability guarantee.
    """
    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("WARNING: Backtest is historical simulation only. Past performance does not guarantee future results.")
    print("=" * 60)

    data = load_csv_strategy_shape(csv_path, symbol=symbol, timeframe=timeframe)
    sym = symbol or list(data.keys())[0]

    strat_class = StrategyRegistry.get(strategy_name)
    cfg = StrategyConfig(
        name=strategy_name,
        symbols=[sym],
        timeframe=timeframe or "H1",
        params=strategy_params or {},
    )
    strategy = strat_class(cfg)

    engine = SimpleBacktestEngine(data, strategy, initial_balance=initial_balance)
    bt_result = engine.run()

    return {
        "status": "ok",
        "symbol": sym,
        "timeframe": timeframe or "UNKNOWN",
        "strategy": strategy_name,
        "backtest": bt_result,
        "disclaimer": "PAPER-ONLY / DATA-ONLY. Backtest is historical simulation only. No profitability guarantee.",
    }
