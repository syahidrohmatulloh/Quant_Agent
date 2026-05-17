"""
Run multiple strategies on the same CSV dataset.
Paper-only. No live trading.
"""
from typing import Dict, Any, List, Optional

from strategy_runtime.csv_strategy_runner import run_strategy_on_csv


def run_batch(
    csv_path: str,
    strategies: List[str],
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    strategy_params_map: Optional[Dict[str, Dict[str, Any]]] = None,
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Run multiple strategies and aggregate results.
    """
    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    results: List[Dict[str, Any]] = []
    params_map = strategy_params_map or {}
    for strat_name in strategies:
        params = params_map.get(strat_name, {})
        r = run_strategy_on_csv(
            csv_path, strat_name,
            symbol=symbol, timeframe=timeframe,
            strategy_params=params, validate=validate,
        )
        results.append(r)

    # Aggregate latest signals
    signals = [r["latest_signal"] for r in results if r.get("latest_signal")]
    return {
        "status": "ok",
        "csv_path": csv_path,
        "strategies_run": strategies,
        "signals": signals,
        "individual_results": results,
        "disclaimer": "PAPER-ONLY / DATA-ONLY. No live trading. No order submission.",
    }
