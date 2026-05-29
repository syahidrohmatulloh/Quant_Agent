"""Simulator engine: orchestrates the full paper simulation pipeline.

Paper-only. No live trading. No order submission.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from paper_simulator.simulator_config import validate_simulator_config
from paper_simulator.price_loader import PriceLoader
from paper_simulator.order_intent import build_order_intents, OrderIntent
from paper_simulator.fill_model import simulate_fill, FillResult
from paper_simulator.position_book import PositionBook
from paper_simulator.pnl_engine import compute_pnl, PnlSnapshot
from paper_simulator.exposure import compute_exposure, ExposureReport
from paper_simulator.simulator_log import append_trade_log, append_pnl_log
from paper_simulator.simulator_report import generate_report
from paper_simulator.dashboard_export import export_dashboard_json


class SimulatorEngine:
    """End-to-end paper portfolio simulator engine."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.position_book = PositionBook(config["portfolio_state_path"])
        self.price_loaders: Dict[str, PriceLoader] = {}
        self.latest_fills: List[FillResult] = []
        self.latest_intents: List[OrderIntent] = []
        self.latest_pnl: Optional[PnlSnapshot] = None
        self.latest_exposure: Optional[ExposureReport] = None
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def _load_prices(self):
        for sym_cfg in self.config.get("symbols", []):
            csv_path = sym_cfg["csv"]
            try:
                loader = PriceLoader(
                    csv_path,
                    symbol=sym_cfg.get("symbol"),
                    timeframe=sym_cfg.get("timeframe"),
                )
                self.price_loaders[sym_cfg["symbol"]] = loader
            except Exception as e:
                self.warnings.append("Failed to load prices for " + sym_cfg["symbol"] + ": " + str(e))

    def _get_fill_price(self, symbol: str, decision_timestamp: Optional[datetime] = None) -> Optional[float]:
        mode = self.config.get("execution", {}).get("fill_price", "next_close")
        loader = self.price_loaders.get(symbol)
        if loader is None:
            return None
        if mode == "current_close":
            return loader.latest_close()
        elif mode == "next_close":
            if decision_timestamp:
                return loader.next_close(decision_timestamp)
            return loader.latest_close()
        elif mode == "midpoint_close":
            latest = loader.latest_bar()
            if latest:
                high = latest.get("high")
                low = latest.get("low")
                if high is not None and low is not None:
                    return (high + low) / 2.0
            return loader.latest_close()
        return loader.latest_close()

    def run(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run the full simulation pipeline."""
        print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

        self._load_prices()

        # 1. Validate config
        ok, errors, warnings = validate_simulator_config(self.config)
        if not ok:
            self.errors.extend(errors)
            self.warnings.extend(warnings)
            return self._build_summary()

        # 2. Convert decisions to intents
        risk_config = self.config.get("risk", {})
        initial_cash = self.config.get("initial_cash", 100000.0)
        self.latest_intents = build_order_intents(decisions, risk_config, initial_cash)

        # 3. Apply risk constraints (symbol weight, max notional)
        filtered_intents = self._apply_risk(self.latest_intents)

        # 4. Simulate fills
        costs_config = self.config.get("costs", {})
        for intent in filtered_intents:
            if intent.side in ("HOLD", "REJECTED"):
                continue
            sym_cfg = self._get_symbol_config(intent.symbol)
            if sym_cfg is None:
                self.warnings.append("No symbol config for " + intent.symbol)
                continue
            price = self._get_fill_price(intent.symbol)
            if price is None:
                self.warnings.append("No price available for " + intent.symbol + "; fill skipped.")
                continue
            fill = simulate_fill(intent, price, costs_config, sym_cfg)
            if fill is not None:
                self.latest_fills.append(fill)
                # Update position book
                self.position_book.update_position(
                    symbol=intent.symbol,
                    timeframe=intent.timeframe,
                    side=intent.side,
                    quantity=intent.target_notional / price,
                    price=price,
                    fill_cost=fill.total_cost,
                )

        # 5. Mark to market all positions
        latest_prices: Dict[str, float] = {}
        for sym, loader in self.price_loaders.items():
            close = loader.latest_close()
            if close is not None:
                latest_prices[sym] = close
            else:
                self.warnings.append("Missing latest close for " + sym)

        for pos in self.position_book.all_positions():
            price = latest_prices.get(pos.symbol)
            if price is not None:
                self.position_book.mark_to_market(pos.symbol, pos.timeframe, price)

        # 6. Compute PnL
        self.latest_pnl = compute_pnl(
            self.position_book, latest_prices, initial_cash, self.config.get("base_currency", "USD")
        )
        if self.latest_pnl.warnings:
            self.warnings.extend(self.latest_pnl.warnings)

        # 7. Compute exposure
        self.latest_exposure = compute_exposure(
            self.position_book, latest_prices, risk_config, initial_cash
        )
        if self.latest_exposure.warnings:
            self.warnings.extend(self.latest_exposure.warnings)

        # 8. Append logs
        for fill in self.latest_fills:
            append_trade_log(fill.to_dict(), self.config["trade_log_path"])
        if self.latest_pnl:
            append_pnl_log(self.latest_pnl.to_dict(), self.config["pnl_log_path"])

        # 9. Save position book
        self.position_book.save()

        # 10. Generate report
        report_path = self.config.get("report_output", "reports/paper_simulator/paper_simulator_report.md")
        generate_report(
            config=self.config,
            decisions=decisions,
            intents=self.latest_intents,
            fills=self.latest_fills,
            position_book=self.position_book,
            pnl=self.latest_pnl,
            exposure=self.latest_exposure,
            output_path=report_path,
        )

        # 11. Export dashboard JSON
        dashboard_path = self.config.get("dashboard_output", "reports/dashboard/paper_simulator/latest.json")
        export_dashboard_json(
            config=self.config,
            position_book=self.position_book,
            fills=self.latest_fills,
            pnl=self.latest_pnl,
            exposure=self.latest_exposure,
            warnings=self.warnings,
            errors=self.errors,
            output_path=dashboard_path,
        )

        return self._build_summary()

    def _apply_risk(self, intents: List[OrderIntent]) -> List[OrderIntent]:
        """Apply risk constraints to intents."""
        risk = self.config.get("risk", {})
        max_notional = risk.get("max_notional_per_symbol", float("inf"))
        allow_short = risk.get("allow_short", True)
        filtered = []
        for intent in intents:
            if intent.side == "SELL" and not allow_short:
                intent.side = "REJECTED"
                intent.reason = "Short intent rejected because allow_short is false."
            if intent.target_notional > max_notional:
                intent.target_notional = max_notional
                intent.reason += " (capped by max_notional_per_symbol)."
            filtered.append(intent)
        return filtered

    def _get_symbol_config(self, symbol: str) -> Optional[Dict[str, Any]]:
        for sym in self.config.get("symbols", []):
            if sym.get("symbol") == symbol:
                return sym
        return None

    def _build_summary(self) -> Dict[str, Any]:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "paper_only": True,
            "data_only": True,
            "no_order_submission": True,
            "decisions_processed": len(self.latest_intents),
            "fills_simulated": len(self.latest_fills),
            "positions_count": len(self.position_book.all_positions()),
            "warnings": self.warnings,
            "errors": self.errors,
        }
