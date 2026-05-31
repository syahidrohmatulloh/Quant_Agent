"""
Research Insights module for Quant_Agent Phase 26.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Builds structured research insight summaries from existing local outputs.
"""
from research_insights.insight_builder import (
    ResearchInsightSummary,
    StrategyInsight,
    build_research_insights,
    classify_strategy_metrics,
    render_research_insights_summary,
    load_strategy_outputs,
)

__all__ = [
    "ResearchInsightSummary",
    "StrategyInsight",
    "build_research_insights",
    "classify_strategy_metrics",
    "render_research_insights_summary",
    "load_strategy_outputs",
]
