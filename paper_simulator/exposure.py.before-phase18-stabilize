"""Exposure reporting for paper simulation.

Risk warnings: gross/net exposure, symbol concentration, short exposure, missing data.
"""
DEFAULT_CONTRACT_SIZE = 100000.0

from typing import Dict, Any, List, Optional

from paper_simulator.position_book import PositionBook


class ExposureReport:
    """Exposure report with risk warnings."""

    def __init__(
        self,
        gross_exposure: float,
        net_exposure: float,
        long_exposure: float,
        short_exposure: float,
        exposure_by_symbol: Dict[str, float],
        exposure_by_timeframe: Dict[str, float],
        max_concentration: float,
        max_concentration_symbol: str,
        warnings: List[str],
    ):
        self.gross_exposure = gross_exposure
        self.net_exposure = net_exposure
        self.long_exposure = long_exposure
        self.short_exposure = short_exposure
        self.exposure_by_symbol = exposure_by_symbol
        self.exposure_by_timeframe = exposure_by_timeframe
        self.max_concentration = max_concentration
        self.max_concentration_symbol = max_concentration_symbol
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gross_exposure": self.gross_exposure,
            "net_exposure": self.net_exposure,
            "long_exposure": self.long_exposure,
            "short_exposure": self.short_exposure,
            "exposure_by_symbol": self.exposure_by_symbol,
            "exposure_by_timeframe": self.exposure_by_timeframe,
            "max_concentration": self.max_concentration,
            "max_concentration_symbol": self.max_concentration_symbol,
            "warnings": self.warnings,
        }


def compute_exposure(
    position_book: PositionBook,
    latest_prices: Dict[str, float],
    risk_config: Dict[str, Any],
    initial_cash: float,
) -> ExposureReport:
    """Compute exposure report from position book and latest prices."""
    warnings: List[str] = []
    gross = 0.0
    net = 0.0
    long_exp = 0.0
    short_exp = 0.0
    by_symbol: Dict[str, float] = {}
    by_timeframe: Dict[str, float] = {}

    allow_short = risk_config.get("allow_short", True)
    max_symbol_weight = risk_config.get("max_symbol_weight", 0.25)
    max_total_gross = risk_config.get("max_total_gross_exposure", 1.0)

    for pos in position_book.all_positions():
        price = latest_prices.get(pos.symbol, 0.0)
        if price is None or price == 0:
            warnings.append("No recent price data for " + pos.symbol + "; exposure may be stale.")
            continue

        notional = pos.quantity * price * DEFAULT_CONTRACT_SIZE
        if pos.side == "LONG":
            long_exp += notional
            net += notional
        elif pos.side == "SHORT":
            short_exp += notional
            net -= notional
            if not allow_short:
                warnings.append("Short exposure detected for " + pos.symbol + " but allow_short is false.")
        gross += notional

        by_symbol[pos.symbol] = by_symbol.get(pos.symbol, 0.0) + notional
        by_timeframe[pos.timeframe] = by_timeframe.get(pos.timeframe, 0.0) + notional

    max_conc = 0.0
    max_sym = ""
    for sym, exp in by_symbol.items():
        weight = exp / initial_cash if initial_cash > 0 else 0.0
        if weight > max_symbol_weight:
            warnings.append(
                "Symbol exposure for " + sym + " (" + str(round(weight * 100, 2)) + "%) exceeds limit ("
                + str(round(max_symbol_weight * 100, 2)) + "%)."
            )
        if weight > max_conc:
            max_conc = weight
            max_sym = sym

    gross_weight = gross / initial_cash if initial_cash > 0 else 0.0
    if gross_weight > max_total_gross:
        warnings.append(
            "Gross exposure (" + str(round(gross_weight * 100, 2)) + "%) exceeds limit ("
            + str(round(max_total_gross * 100, 2)) + "%)."
        )

    return ExposureReport(
        gross_exposure=round(gross, 2),
        net_exposure=round(net, 2),
        long_exposure=round(long_exp, 2),
        short_exposure=round(short_exp, 2),
        exposure_by_symbol={k: round(v, 2) for k, v in by_symbol.items()},
        exposure_by_timeframe={k: round(v, 2) for k, v in by_timeframe.items()},
        max_concentration=round(max_conc, 4),
        max_concentration_symbol=max_sym,
        warnings=warnings,
    )
