"""
View models / data structures for the Phase 14 dashboard.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class DatasetViewModel:
    dataset_id: str
    filename: str
    path: str
    symbol: str
    timeframe: str
    source: str
    row_count: int
    valid: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ExperimentConfigViewModel:
    path: str
    name: str
    valid: bool
    paper_only: bool
    data_only: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ExperimentHistoryViewModel:
    run_id: str
    generated_at: str
    experiment_name: str
    symbol_count: int
    strategy_count: int
    result_path: Optional[str]
    dashboard_json_path: Optional[str]


@dataclass
class ReportViewModel:
    report_id: str
    title: str
    generated_at: Optional[str]
    path: str


@dataclass
class HomeStatusViewModel:
    dataset_count: int
    experiment_report_count: int
    dashboard_export_count: int
    latest_experiment_name: Optional[str]
    latest_experiment_time: Optional[str]
