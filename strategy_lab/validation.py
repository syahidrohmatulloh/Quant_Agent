"""
Validate strategy registry, config, signal shape, and output sanity.
"""
from typing import Dict, Any, List
import math
from strategies.base import StrategyConfig, StrategyResult, StrategySignal
from strategies.registry import StrategyRegistry


def validate_registry() -> Dict[str, Any]:
    return StrategyRegistry.validate_all()


def validate_config(config: StrategyConfig) -> List[str]:
    errors = []
    try:
        config.validate()
    except ValueError as e:
        errors.append(str(e))
    if config.paper_only is not True:
        errors.append("Config must have paper_only=True")
    return errors


def validate_signal_shape(result: StrategyResult, expected_symbols: List[str]) -> List[str]:
    errors = []
    seen = set()
    for sig in result.signals:
        if not isinstance(sig, StrategySignal):
            errors.append(f"Invalid signal type: {type(sig)}")
            continue
        if sig.signal not in ("buy", "sell", "hold", "long", "short", "flat", "close"):
            errors.append(f"Unknown signal value: {sig.signal}")
        if sig.weight < -1.0 or sig.weight > 1.0:
            errors.append(f"Weight out of bounds for {sig.symbol}: {sig.weight}")
        if math.isnan(sig.weight) or math.isinf(sig.weight):
            errors.append(f"NaN/Inf weight for {sig.symbol}")
        seen.add(sig.symbol)
    missing = set(expected_symbols) - seen
    if missing:
        errors.append(f"Missing signals for symbols: {missing}")
    return errors


def validate_no_nan_inf(result: StrategyResult) -> List[str]:
    errors = []
    for sig in result.signals:
        if math.isnan(sig.weight) or math.isinf(sig.weight):
            errors.append(f"NaN/Inf in signal weight for {sig.symbol}")
    return errors
