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
  - `render_research_insights_summary()` — human-readable CLI output with safety disclaimers
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

## Phase 27
- Paper Runtime Monitoring and Session Journal
- Added `paper_runtime/session_journal.py` module for local paper-runtime session tracking
  - `PaperRuntimeSession` dataclass — captures workflow status, signals, decisions, portfolio, PnL, exposure, risk warnings
  - `PaperRuntimeJournal` dataclass — aggregates sessions with counts and paths
  - `build_paper_runtime_session()` — reads existing local outputs and builds session
  - `build_paper_runtime_journal()` — builds journal from sessions
  - `write_paper_runtime_journal()` — writes JSONL, latest JSON, and Markdown summaries
  - `render_paper_runtime_summary()` — human-readable CLI output with safety disclaimers
  - `load_latest_paper_runtime_session()` — loads latest session from disk
- Added `tools/show_paper_runtime_journal.py` CLI tool
  - `--allow-missing` tolerates missing optional outputs
  - `--write-journal` writes outputs to `reports/paper_runtime/`
  - Returns 0 if no critical blockers, non-zero only for config/safety failure
- Enhanced `dashboard/routes.py` with `/paper-runtime` route
- Enhanced `dashboard/templates.py` with `render_paper_runtime()` HTML page
- Added nav links from `/`, `/operator`, `/action-center`, `/research-insights` to `/paper-runtime`
- Enhanced `local_app/action_center.py` with paper runtime action items and latest session path
- Enhanced `local_app/operator_status.py` with paper runtime status and path
- Safety wording enforced throughout:
  - PAPER-ONLY / DATA-ONLY on every output
  - No live trading
  - No order submission
  - Not financial advice
  - Does not approve or enable live trading
  - Does not guarantee performance
- Added tests:
  - `tests/paper_runtime/test_phase27_session_journal.py`
  - `tests/dashboard/test_phase27_paper_runtime_dashboard.py`
  - `tests/tools/test_phase27_paper_runtime_cli.py`
- Updated docs: DAILY_WORKFLOW, COMMAND_CHEATSHEET, PHASE_HISTORY
- All changes remain paper-only / data-only
- No live trading, no order submission, no broker calls, no email/Telegram send, no cron
- No generated outputs committed

## Phase 28
- Data Quality Center for Market Data CSV Validation
- Added `data_quality/` module for structured data quality scanning
  - `quality_report.py` with `DataQualityIssue`, `DataQualityFileSummary`, and `DataQualityReport` dataclasses
  - `scan_market_data_file()` — scans a single CSV for all quality issues
  - `scan_market_data_directory()` — scans all CSVs in a directory
  - `classify_data_quality()` — classifies overall status: OK | WARN | BLOCKED
  - `build_data_quality_report()` — builds comprehensive report for all configured directories
  - `render_data_quality_summary()` — human-readable CLI output with safety disclaimers
  - `write_data_quality_report()` — writes JSON, Markdown, and dashboard latest.json
  - `load_latest_data_quality_report()` — loads latest report from disk
  - Quality checks implemented:
    - Missing data directories
    - Empty files
    - Malformed CSV (parse errors, invalid encoding)
    - Missing OHLC columns
    - Duplicate timestamps
    - Non-monotonic timestamps
    - Zero/negative prices
    - High < low violations
    - Close outside high/low range
    - Insufficient rows (configurable minimum)
    - Stale data (configurable hour threshold)
    - Timezone ambiguity (timestamps without explicit timezone)
- Added `tools/show_data_quality.py` CLI tool
  - `--config` required: path to market data import config JSON
  - `--allow-missing` tolerates missing optional data directories and files
  - `--write-report` writes JSON + Markdown + dashboard latest.json
  - Validates `paper_only`, `data_only`, `no_order_submission` must be true
  - Returns 0 on success, 2 on BLOCKED status, 1 on config/safety failure
- Enhanced `dashboard/routes.py` with `/data-quality` route
  - Reads `examples/market_data_import_config.example.json`
  - Shows empty state with guidance if config missing
  - Displays quality report with all file summaries, issues, warnings, blockers
- Enhanced `dashboard/templates.py` with `render_data_quality()` HTML page
  - File report table: filename, status, rows, columns, dupes, non-mono, missing cols, zero/neg, invalid OHLC, start, end
  - Issues table with severity, category, message, suggested action
  - Summary: files scanned, status
  - Warnings, blockers, data quality notes, generated outputs
  - Next safe commands
  - Nav links to all other dashboard pages
  - Safety disclaimers throughout
- Added nav links from `/`, `/operator`, `/action-center`, `/research-insights`, `/paper-runtime` to `/data-quality`
- Added tests:
  - `tests/data_quality/test_phase28_quality_report.py` — 14 test classes covering:
    - CSV read (valid, missing, empty)
    - Timestamp column detection
    - Timestamp parsing (ISO, MT5, invalid)
    - Timezone info detection
    - Scan market data file (valid, missing OHLC, dupes, non-mono, zero/neg prices, high < low, close outside range, empty, malformed, missing)
    - Scan market data directory (scans, empty, nonexistent)
    - Classify data quality (OK, WARN, BLOCKED)
    - Build data quality report (no datasets, scans configured, detects missing dir, stale data, insufficient rows, timezone ambiguity)
    - Render data quality summary (includes paper-only, no live trading, next safe commands, file summaries)
    - Write data quality report (writes JSON, Markdown, dashboard latest)
    - Load latest data quality report (loads existing, returns none when missing)
    - No hardcoded paths / no forbidden raw literals
  - `tests/dashboard/test_phase28_data_quality_dashboard.py` — 15 tests covering:
    - Route exists, paper-only disclaimer, not financial advice, header, next safe commands, no live trading
    - Empty state, health unchanged, home links, operator links, action-center links, research-insights links, paper-runtime links
  - `tests/tools/test_phase28_data_quality_cli.py` — 10 tests covering:
    - Runs with allow-missing, output contains paper-only/data-only, header, no live trading
    - Returns nonzero for missing config, write-report creates files, no credentials required
    - No hardcoded paths, no forbidden raw literals, docs mention data quality
- Updated docs: DAILY_WORKFLOW, COMMAND_CHEATSHEET, PHASE_HISTORY
- All changes remain paper-only / data-only
- No live trading, no order submission, no broker calls, no email/Telegram send, no cron
- No generated outputs committed

## Phase 29
- Paper Broker Integration Hardening
- Added `paper_broker/` module for paper broker readiness validation
  - `readiness.py` with `PaperBrokerCheck` and `PaperBrokerReadinessReport` dataclasses
  - `build_paper_broker_readiness()` — builds readiness report from config and local checks
  - `validate_paper_broker_config()` — validates paper_only, data_only, no_order_submission, mode checks
  - `validate_adapter_contract()` — checks required paper methods, blocks forbidden execution methods
  - `detect_credential_like_values()` — detects real credentials in config, allows placeholders
  - `simulate_paper_connectivity()` — local-only connectivity simulation, no network calls
  - `classify_paper_broker_readiness()` — READY | READY_WITH_WARNINGS | BLOCKED
  - `render_paper_broker_readiness_summary()` — human-readable CLI output with safety disclaimers
  - `write_paper_broker_readiness_report()` — writes JSON, Markdown, and dashboard latest.json
  - `load_latest_paper_broker_readiness()` — loads latest report from disk
- Added `tools/show_paper_broker_readiness.py` CLI tool
  - `--config` required: path to config JSON
  - `--allow-missing` tolerates missing optional broker config
  - `--write-report` writes outputs to `reports/paper_broker/`
  - Validates `paper_only`, `data_only`, `no_order_submission` must be true
  - Returns 0 for READY or READY_WITH_WARNINGS, 2 for BLOCKED, 1 for config/safety failure
- Enhanced `dashboard/routes.py` with `/paper-broker` route
  - Reads `examples/local_app_config.example.json`
  - Shows readiness report with checks, warnings, blockers, next safe commands
- Enhanced `dashboard/templates.py` with `render_paper_broker()` HTML page
  - Status badge, broker name/mode, config path
  - Checks table with name, status, category, message, suggested action
  - Warnings, blockers, generated outputs, next safe commands
  - Nav links to all other dashboard pages
  - Safety disclaimers throughout
- Added nav links from `/`, `/operator`, `/action-center`, `/research-insights`, `/paper-runtime`, `/data-quality` to `/paper-broker`
- Safety wording enforced throughout:
  - PAPER-ONLY / DATA-ONLY on every output
  - No live trading
  - No order submission
  - Not financial advice
  - Does not approve or enable live trading
  - Does not guarantee performance
  - No credentials required
  - No real broker execution
- Added tests:
  - `tests/paper_broker/test_phase29_paper_broker_readiness.py`
  - `tests/dashboard/test_phase29_paper_broker_dashboard.py`
  - `tests/tools/test_phase29_paper_broker_readiness_cli.py`
- Updated docs: DAILY_WORKFLOW, COMMAND_CHEATSHEET, PHASE_HISTORY
- All changes remain paper-only / data-only
- No live trading, no order submission, no broker calls, no email/Telegram send, no cron
- No generated outputs committed

## Phase 30
- Local MVP Release Candidate Hardening
- Added `release_candidate/` module for final release-readiness validation
  - `checklist.py` with `ReleaseCandidateCheck` and `ReleaseCandidateReport` dataclasses
  - `build_release_candidate_report()` — builds readiness report from local checks
  - `check_required_docs()` — verifies README, COMMAND_CHEATSHEET, DAILY_WORKFLOW, PHASE_HISTORY exist
  - `check_generated_outputs_clean()` — warns on reports/, logs/, local_configs/, backups/, data/market_versions/
  - `check_dashboard_routes_available()` — verifies all expected dashboard routes present
  - `check_cli_tools_present()` — verifies all operator and research CLI tools exist
  - `check_safety_phrases()` — verifies key docs contain required safety disclaimers
  - `check_release_tags()` — reminds about git tag phase-29-clean
  - `classify_release_candidate()` — READY | READY_WITH_WARNINGS | BLOCKED
  - `render_release_candidate_summary()` — human-readable CLI output with safety disclaimers
  - `write_release_candidate_report()` — writes JSON, Markdown, and dashboard latest.json
  - `load_latest_release_candidate_report()` — loads latest report from disk
- Added `tools/run_release_candidate_check.py` CLI tool
  - `--config` required: path to config JSON
  - `--allow-missing` tolerates missing optional docs/tools
  - `--write-report` writes outputs to `reports/release_candidate/`
  - `--smoke` runs safe py_compile smoke checks without network or credentials
  - Validates `paper_only`, `data_only`, `no_order_submission` must be true
  - Returns 0 for READY or READY_WITH_WARNINGS, 2 for BLOCKED, 1 for config/safety failure
- Enhanced `dashboard/routes.py` with `/release-candidate` route
  - Reads `examples/local_app_config.example.json`
  - Shows release candidate report with checks, warnings, blockers, next safe commands
  - Builds safe in-memory report if no existing report on disk
- Enhanced `dashboard/templates.py` with `render_release_candidate()` HTML page
  - Status badge, version label, baseline tag
  - Checks table with name, status, category, message, suggested action
  - Warnings, blockers, generated output cleanup reminder, next safe commands
  - Nav links to all other dashboard pages
  - Safety disclaimers throughout
- Added nav links from `/`, `/operator`, `/action-center`, `/research-insights`, `/paper-runtime`, `/data-quality`, `/paper-broker` to `/release-candidate`
- Safety wording enforced throughout:
  - PAPER-ONLY / DATA-ONLY on every output
  - No live trading
  - No order submission
  - Not financial advice
  - Does not approve or enable live trading
  - Does not guarantee performance
  - No credentials required
  - No real broker execution
- Added tests:
  - `tests/release_candidate/test_phase30_release_candidate.py`
  - `tests/dashboard/test_phase30_release_candidate_dashboard.py`
  - `tests/tools/test_phase30_release_candidate_cli.py`
- Updated docs: DAILY_WORKFLOW, COMMAND_CHEATSHEET, PHASE_HISTORY, SAFETY_AND_LIMITATIONS, DEMO_SCRIPT
- All changes remain paper-only / data-only
- No live trading, no order submission, no broker calls, no email/Telegram send, no cron
- No generated outputs committed
- This phase is release hardening only; no new product modules added

## Phase 30A
- Quant Correctness & Reliability Hardening
- Corrected paper-simulator exposure so contract size is applied exactly once.
- Reworked paper position/PnL accounting so realized PnL, unrealized PnL, and transaction costs reconcile without lost or double-counted costs.
- Made `next_close` fills causal: historical decisions require the next valid bar after the decision timestamp and no longer fall back to the latest dataset close.
- Fixed paper neutral/flatten quantity handling.
- Fixed backtest position lifecycle so closed positions are removed and repeated same-direction fills aggregate consistently.
- Fixed Strategy Lab equity accounting to avoid cumulative unrealized-PnL double counting and moved commission calculation to traded notional.
- Hardened risk input validation and projected-exposure checks.
- Hardened `/manual/order` role enforcement to operator/admin and corrected audit actor attribution.
- Made paper-broker safety flags and mode checks fail closed; added explicit safe `paper_broker_config.example.json`.
- Hardened OANDA practice endpoint validation to an exact HTTPS practice hostname and removed duplicate adapter health-check implementation.
- Added the missing `requests` runtime dependency used by HTTP transport.
- Made audit hash chains resume across process restarts and retain full SHA-256 hashes while the validator remains compatible with legacy truncated hashes.
- Added timeframe-aware performance annualization and a walk-forward training hook so training windows are no longer silently unused.
- Fixed binary-class signal mapping so class `0` in a `{0,1}` model maps to SELL rather than producing a non-actionable HOLD order.
- Added `tests/quant_correctness/test_phase30a_quant_correctness.py` with financial and safety regression invariants.
- Added GitHub Actions CI for dependency install, source compilation, and the full pytest suite.
- Remains PAPER-ONLY / DATA-ONLY. No live real-money trading is enabled by this phase.
