"""Strategy attribution analysis.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from typing import Dict, List, Any, Optional


def analyze_strategy_attribution(
    strategy_results: Dict[str, Dict[str, Any]],
    by_symbol: Optional[Dict[str, Dict[str, Any]]] = None,
    by_timeframe: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    warnings = []

    # Contribution by strategy
    contrib_strategy = {}
    for name, data in strategy_results.items():
        ret = data.get("total_return", 0.0)
        contrib_strategy[name] = round(ret, 6)

    # Contribution by symbol
    contrib_symbol = {}
    if by_symbol:
        for sym, data in by_symbol.items():
            contrib_symbol[sym] = round(data.get("total_return", 0.0), 6)

    # Contribution by timeframe
    contrib_tf = {}
    if by_timeframe:
        for tf, data in by_timeframe.items():
            contrib_tf[tf] = round(data.get("total_return", 0.0), 6)

    # Consensus vs individual
    names = list(strategy_results.keys())
    consensus = {}
    if names:
        n = len(names)
        for name in names:
            others = [k for k in names if k != name]
            if others:
                avg_other = sum(strategy_results[k].get("total_return", 0.0) for k in others) / len(others)
                consensus[name] = round(strategy_results[name].get("total_return", 0.0) - avg_other, 6)

    # Agreement / conflict ratio
    agreement = 0
    conflict = 0
    total_pairs = 0
    if len(names) > 1:
        signals_map = {k: v.get("signals", []) for k, v in strategy_results.items()}
        lengths = [len(v) for v in signals_map.values()]
        if lengths and min(lengths) == max(lengths) and max(lengths) > 0:
            L = lengths[0]
            for i in range(L):
                sigs = [signals_map[k][i] for k in names]
                for a in range(len(sigs)):
                    for b in range(a + 1, len(sigs)):
                        total_pairs += 1
                        if sigs[a] == sigs[b]:
                            agreement += 1
                        else:
                            conflict += 1

    agreement_ratio = agreement / total_pairs if total_pairs else None
    conflict_ratio = conflict / total_pairs if total_pairs else None

    best = None
    worst = None
    if contrib_strategy:
        best = max(contrib_strategy, key=contrib_strategy.get)
        worst = min(contrib_strategy, key=contrib_strategy.get)

    if len(strategy_results) < 3:
        warnings.append("Small number of strategies; attribution may be unstable.")

    return {
        "contribution_by_strategy": contrib_strategy,
        "contribution_by_symbol": contrib_symbol,
        "contribution_by_timeframe": contrib_tf,
        "consensus_vs_individual": consensus,
        "agreement_ratio": round(agreement_ratio, 6) if agreement_ratio is not None else None,
        "conflict_ratio": round(conflict_ratio, 6) if conflict_ratio is not None else None,
        "best_strategy_historical": best,
        "worst_strategy_historical": worst,
        "warnings": warnings,
        "note": "No ranking implies future performance. Historical simulation only.",
    }
