# Phase History

## Phase 1-13
- Initial architecture
- Core modules
- Safety gates

## Phase 14
- Local dashboard

## Phase 15
- Paper orchestration

## Phase 16
- Data manager

## Phase 17
- Research analytics

## Phase 18
- Paper simulator

## Phase 19
- Daily briefing

## Phase 20
- Local app workflow and status tools

## Phase 21
- Local config validation and directory initialization

## Phase 22
- Readiness audit CLI and safety improvements

## Phase 23
- Dashboard export, readiness log, and test coverage improvements

## Phase 24
- Local MVP polish, status clarity, and one-command operator flow
- Added `tools/run_operator_day.py` for single-command daily operation
- Added `local_app/operator_status.py` for structured operator status
- Improved `tools/show_local_app_status.py` and `local_app/status_summary.py` with clearer sections
- Added operator status card to dashboard (`/operator` route)
- Updated docs: DAILY_WORKFLOW, COMMAND_CHEATSHEET, PHASE_HISTORY
- All changes remain paper-only / data-only
- No live trading, no order submission, no broker calls, no email/Telegram send, no cron

## Phase 25
- Action center for categorized warnings, blockers, and action items
- Added `local_app/action_center.py` with pure, testable utilities
  - `categorize_readiness_findings()` — stable 6-category classification
  - `build_operator_action_center()` — structured action center from local outputs
  - `render_action_center_summary()` — human-readable CLI output
- Enhanced `local_app/operator_status.py` with Phase 25 fields
  - `warning_categories`, `readiness_action_items`, `workflow_action_items`
  - `briefing_action_items`, `dashboard_action_items`, `latest_operator_run`
  - Backward-compatible: all new fields have safe defaults
- Added `tools/show_action_center.py` CLI tool
- Enhanced `dashboard/templates.py` with `render_action_center()` HTML page
- Enhanced `dashboard/routes.py` with `/action-center` route
- Fixed `render_operator_status()` in templates: uses `html.escape()` correctly
- Added nav link from `/operator` to `/action-center`
- Added tests:
  - `tests/local_app/test_phase25_action_center.py`
  - `tests/dashboard/test_phase25_dashboard.py`
  - `tests/tools/test_phase25_action_center_cli.py`
- Updated docs: DAILY_WORKFLOW, COMMAND_CHEATSHEET, PHASE_HISTORY
- All changes remain paper-only / data-only
- No live trading, no order submission, no broker calls, no email/Telegram send, no cron

## Phase 26
- Research Insights Dashboard and Strategy Comparison UX
- Added `research_insights/` module for structured research insight summaries
  - `insight_builder.py` with `ResearchInsightSummary` and `StrategyInsight` dataclasses
  - `build_research_insights()` — reads existing local outputs and builds summaries
  - `classify_strategy_metrics()` — safe paper-only classification logic
  - `render_research_insights_summary()` — human-readable CLI output
  - `load_strategy_outputs()` — scans reports/experiments, reports/research_analytics, etc.
- Added `tools/show_research_insights.py` CLI tool
- Enhanced `dashboard/routes.py` with `/research-insights` route
- Enhanced `dashboard/templates.py` with `render_research_insights()` HTML page
- Added nav links from `/`, `/operator`, and `/action-center` to `/research-insights`
- Classification values:
  - `candidate_for_further_paper_testing`
  - `monitor_in_paper_mode`
  - `needs_more_data`
  - `inconclusive`
  - `weak_paper_metrics`
- Safety wording enforced:
  - No buy/sell recommendations
  - No live trading advice
  - No profitability guarantees
  - No capital allocation advice
- Added tests:
  - `tests/research/test_phase26_research_insights.py`
  - `tests/dashboard/test_phase26_research_insights_dashboard.py`
  - `tests/tools/test_phase26_research_insights_cli.py`
- Updated docs: DAILY_WORKFLOW, COMMAND_CHEATSHEET, PHASE_HISTORY
- All changes remain paper-only / data-only
- No live trading, no order submission, no broker calls, no email/Telegram send, no cron
- No generated outputs committed
