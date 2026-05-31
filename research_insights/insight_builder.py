"""
Research Insights builder for Phase 26.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Reads existing local research/experiment outputs and builds structured summaries.
Does not make network calls. Does not require real market data.
Does not delete anything. Tolerates missing optional outputs.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class StrategyInsight:
    """Single strategy insight from research outputs."""
    name: str = ""
    source: str = ""
    score: Optional[float] = None
    return_metric: Optional[float] = None
    drawdown_metric: Optional[float] = None
    sharpe_metric: Optional[float] = None
    win_rate_metric: Optional[float] = None
    sample_size: Optional[int] = None
    data_quality: str = "unknown"
    classification: str = "inconclusive"
    reason: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class ResearchInsightSummary:
    """Aggregated research insight summary."""
    generated_at: str = ""
    paper_only: bool = True
    data_only: bool = True
    no_order_submission: bool = True
    source_paths: List[str] = field(default_factory=list)
    strategies: List[StrategyInsight] = field(default_factory=list)
    top_candidates: List[str] = field(default_factory=list)
    weak_candidates: List[str] = field(default_factory=list)
    inconclusive: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    data_quality_notes: List[str] = field(default_factory=list)
    next_safe_commands: List[str] = field(default_factory=list)


def _read_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Read JSON safely; return None on any error."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _find_latest_file(parent: Path, pattern: str = "*") -> Optional[Path]:
    if not parent.exists():
        return None
    files = sorted(parent.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def classify_strategy_metrics(metrics: Dict[str, Any]) -> str:
    if not metrics:
        return "inconclusive"

    """Classify a strategy based on its paper metrics.

    Returns one of:
    - candidate_for_further_paper_testing
    - monitor_in_paper_mode
    - needs_more_data
    - inconclusive
    - weak_paper_metrics
    """
    sample_size = metrics.get("sample_size") or metrics.get("trades", 0)
    if sample_size is not None and sample_size < 30:
        return "needs_more_data"

    drawdown = metrics.get("drawdown")
    if drawdown is not None and drawdown > 0.25:
        return "weak_paper_metrics"

    sharpe = metrics.get("sharpe")
    win_rate = metrics.get("win_rate")
    ret = metrics.get("return")

    if sharpe is not None and sharpe > 1.0 and win_rate is not None and win_rate > 0.55:
        return "candidate_for_further_paper_testing"

    if sharpe is not None and sharpe > 0.5 and win_rate is not None and win_rate > 0.50:
        return "monitor_in_paper_mode"

    if ret is not None and ret < 0:
        return "weak_paper_metrics"

    return "inconclusive"


def load_strategy_outputs(project_root: Path, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Load strategy outputs from known report directories."""
    outputs: List[Dict[str, Any]] = []
    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")

    # Possible source directories
    search_dirs = [
        reports_dir / "experiments",
        reports_dir / "research_analytics",
        reports_dir / "dashboard" / "research_analytics",
        reports_dir / "strategy_lab",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*.json"):
            data = _read_json_safe(f)
            if data is None:
                continue
            # Look for strategy arrays or single strategy objects
            if isinstance(data, dict):
                # Check for strategies list
                strategies = data.get("strategies", [])
                if isinstance(strategies, list):
                    for s in strategies:
                        if isinstance(s, dict):
                            s["_source_path"] = str(f.relative_to(project_root))
                            outputs.append(s)
                # Check for single strategy metrics
                elif "name" in data or "strategy" in data:
                    data["_source_path"] = str(f.relative_to(project_root))
                    outputs.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        item["_source_path"] = str(f.relative_to(project_root))
                        outputs.append(item)

    return outputs


def build_research_insights(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
    allow_missing: bool = True,
) -> ResearchInsightSummary:
    """Build a ResearchInsightSummary from existing local outputs."""
    summary = ResearchInsightSummary()
    summary.generated_at = datetime.now(timezone.utc).isoformat()
    summary.paper_only = True
    summary.data_only = True
    summary.no_order_submission = True

    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")

    # Load optional outputs
    strategy_outputs = load_strategy_outputs(project_root, config)
    summary.source_paths = list({s.get("_source_path", "") for s in strategy_outputs})

    # Operator status
    op_status_json = reports_dir / "local_app" / "operator_status.json"
    op_data = _read_json_safe(op_status_json)
    if op_data:
        summary.warnings.extend(op_data.get("warnings", []))
        summary.blockers.extend(op_data.get("blockers", []))

    # Readiness report
    readiness_json = reports_dir / "readiness_gate" / "readiness_report.json"
    readiness_data = _read_json_safe(readiness_json)
    if readiness_data:
        score_data = readiness_data.get("score", {})
        if score_data.get("score") is not None and score_data.get("score") < 50:
            summary.blockers.append("Readiness score below 50. Improve coverage before further research.")
    elif not allow_missing:
        summary.warnings.append("No readiness report found.")

    # Build strategy insights
    for s in strategy_outputs:
        name = s.get("name") or s.get("strategy") or s.get("strategy_name") or "unknown"
        metrics = s.get("metrics", s)  # metrics may be top-level
        if not isinstance(metrics, dict):
            metrics = {}

        classification = classify_strategy_metrics(metrics)
        reason = ""
        if classification == "candidate_for_further_paper_testing":
            reason = "Strong paper metrics: good Sharpe and win rate."
        elif classification == "monitor_in_paper_mode":
            reason = "Moderate paper metrics: worth monitoring in paper mode."
        elif classification == "needs_more_data":
            reason = "Insufficient sample size for reliable classification."
        elif classification == "weak_paper_metrics":
            reason = "Weak paper metrics: high drawdown or negative return."
        else:
            reason = "Metrics are inconclusive."

        insight = StrategyInsight(
            name=name,
            source=s.get("_source_path", ""),
            score=metrics.get("score"),
            return_metric=metrics.get("return"),
            drawdown_metric=metrics.get("drawdown"),
            sharpe_metric=metrics.get("sharpe"),
            win_rate_metric=metrics.get("win_rate"),
            sample_size=metrics.get("sample_size") or metrics.get("trades"),
            data_quality=s.get("data_quality", "unknown"),
            classification=classification,
            reason=reason,
            warnings=[],
        )
        summary.strategies.append(insight)

    # Categorize
    for insight in summary.strategies:
        if insight.classification == "candidate_for_further_paper_testing":
            summary.top_candidates.append(insight.name)
        elif insight.classification == "weak_paper_metrics":
            summary.weak_candidates.append(insight.name)
        elif insight.classification in ("needs_more_data", "inconclusive"):
            summary.inconclusive.append(insight.name)

    # Data quality notes
    if not strategy_outputs:
        summary.warnings.append("No strategy outputs found in reports/experiments, reports/research_analytics, reports/dashboard/research_analytics, or reports/strategy_lab.")
        summary.data_quality_notes.append("No research outputs available yet.")
    else:
        total = len(strategy_outputs)
        with_metrics = sum(1 for s in strategy_outputs if isinstance(s.get("metrics", s), dict))
        summary.data_quality_notes.append(f"Loaded {total} strategy output(s), {with_metrics} with metrics.")

    # Next safe commands
    dashboard_cfg = config.get("dashboard", {}) if config else {}
    host = dashboard_cfg.get("host", "127.0.0.1")
    port = dashboard_cfg.get("port", 8000)
    cfg_str = "examples/local_app_config.example.json"
    if config and config.get("name"):
        cfg_str = "examples/research_analytics_config.example.json"

    summary.next_safe_commands = [
        "python3 tools/show_research_insights.py --config examples/research_analytics_config.example.json --allow-missing",
        f"python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json",
        f"open http://{host}:{port}/research-insights",
    ]

    if not summary.strategies:
        summary.next_safe_commands.insert(
            0,
            "python3 tools/run_research_analytics.py --config examples/research_analytics_config.example.json",
        )

    return summary


def render_research_insights_summary(summary: ResearchInsightSummary) -> str:
    """Render ResearchInsightSummary as a human-readable CLI string."""
    lines = [
        "",
        "=" * 60,
        " QUANT_AGENT RESEARCH INSIGHTS",
        "=" * 60,
        "",
        " PAPER-ONLY / DATA-ONLY",
        " No live trading. No order submission.",
        " This is not financial advice.",
        " This does not approve or enable live trading.",
        " This does not guarantee performance.",
        "",
        f" Generated: {summary.generated_at}",
        f" Sources: {len(summary.source_paths)} path(s)",
        "",
    ]

    if summary.strategies:
        lines.append(" Strategy Insights")
        lines.append("-" * 40)
        for s in summary.strategies:
            lines.append(f"  Name: {s.name}")
            lines.append(f"  Classification: {s.classification}")
            lines.append(f"  Reason: {s.reason}")
            if s.score is not None:
                lines.append(f"  Score: {s.score}")
            if s.sharpe_metric is not None:
                lines.append(f"  Sharpe: {s.sharpe_metric}")
            if s.win_rate_metric is not None:
                lines.append(f"  Win Rate: {s.win_rate_metric}")
            if s.drawdown_metric is not None:
                lines.append(f"  Drawdown: {s.drawdown_metric}")
            if s.sample_size is not None:
                lines.append(f"  Sample Size: {s.sample_size}")
            if s.warnings:
                lines.append(f"  Warnings: {', '.join(s.warnings)}")
            lines.append("")
    else:
        lines.append(" No strategy insights available yet.")
        lines.append("")

    if summary.top_candidates:
        lines.append(" Top Candidates (further paper testing)")
        lines.append("-" * 40)
        for c in summary.top_candidates:
            lines.append(f"  - {c}")
        lines.append("")

    if summary.weak_candidates:
        lines.append(" Weak Candidates (avoid for now)")
        lines.append("-" * 40)
        for c in summary.weak_candidates:
            lines.append(f"  - {c}")
        lines.append("")

    if summary.inconclusive:
        lines.append(" Inconclusive / Needs More Data")
        lines.append("-" * 40)
        for c in summary.inconclusive:
            lines.append(f"  - {c}")
        lines.append("")

    if summary.data_quality_notes:
        lines.append(" Data Quality Notes")
        lines.append("-" * 40)
        for note in summary.data_quality_notes:
            lines.append(f"  - {note}")
        lines.append("")

    if summary.warnings:
        lines.append(f" Warnings ({len(summary.warnings)})")
        lines.append("-" * 40)
        for w in summary.warnings:
            lines.append(f"  - {w}")
        lines.append("")

    if summary.blockers:
        lines.append(f" Blockers ({len(summary.blockers)})")
        lines.append("-" * 40)
        for b in summary.blockers:
            lines.append(f"  ! {b}")
        lines.append("")

    lines.append(" Next Safe Commands")
    lines.append("-" * 40)
    for cmd in summary.next_safe_commands:
        lines.append(f"  $ {cmd}")
    lines.append("")

    lines.append(" Reminder: reports/logs/local outputs should not be committed.")
    lines.append(" This tool does not approve or enable live trading.")
    lines.append(" No broker calls. No live network. No credential prompts.")
    lines.append(" No actual email send. No actual Telegram send. No cron install.")
    lines.append("")
    lines.append("=" * 60)
    lines.append("")
    return "\n".join(lines)
