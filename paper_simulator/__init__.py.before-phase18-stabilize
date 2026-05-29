"""Paper Portfolio Simulator v2.

Simulation-only. No live trading. No broker calls. No order submission.
"""
from .simulator_config import load_simulator_config, validate_simulator_config
from .price_loader import PriceLoader
from .order_intent import build_order_intents, OrderIntent
from .fill_model import simulate_fill, FillResult
from .cost_model import compute_costs, CostBreakdown
from .position_book import PositionBook, Position
from .pnl_engine import compute_pnl, PnlSnapshot
from .exposure import ExposureReport, compute_exposure
from .simulator_engine import SimulatorEngine
from .simulator_report import generate_report
from .simulator_log import append_trade_log, append_pnl_log
from .dashboard_export import export_dashboard_json

__all__ = [
    "load_simulator_config",
    "validate_simulator_config",
    "PriceLoader",
    "build_order_intents",
    "OrderIntent",
    "simulate_fill",
    "FillResult",
    "compute_costs",
    "CostBreakdown",
    "PositionBook",
    "Position",
    "compute_pnl",
    "PnlSnapshot",
    "ExposureReport",
    "compute_exposure",
    "SimulatorEngine",
    "generate_report",
    "append_trade_log",
    "append_pnl_log",
    "export_dashboard_json",
]
