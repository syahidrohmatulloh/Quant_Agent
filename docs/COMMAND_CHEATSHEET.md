# Command Cheatsheet

## Data Quality Center (Phase 28)
- `python3 tools/show_data_quality.py --config examples/market_data_import_config.example.json`
- `python3 tools/show_data_quality.py --config examples/market_data_import_config.example.json --allow-missing`
- `python3 tools/show_data_quality.py --config examples/market_data_import_config.example.json --allow-missing --write-report`

## Paper Runtime Journal (Phase 27)
- `python3 tools/show_paper_runtime_journal.py --config examples/local_app_config.example.json --allow-missing`
- `python3 tools/show_paper_runtime_journal.py --config examples/local_app_config.example.json --allow-missing --write-journal`

## Research Insights (Phase 26)
- `python3 tools/show_research_insights.py --config examples/research_analytics_config.example.json --allow-missing`

## Operator Day (Phase 24)
- `python3 tools/run_operator_day.py --config examples/local_app_config.example.json --allow-missing`

## Action Center (Phase 25)
- `python3 tools/show_action_center.py --config examples/local_app_config.example.json --allow-missing`

## Data Collection
- `python3 tools/run_data_collection.py --config examples/data_collection_config.example.json`

## Research Analytics
- `python3 tools/run_research_analytics.py --config examples/research_analytics_config.example.json`

## Paper Simulator
- `python3 tools/run_paper_simulator.py --config examples/paper_simulator_config.example.json`

## Daily Briefing
- `python3 tools/generate_daily_briefing.py --config examples/briefing_config.example.json`

## Readiness Audit
- `python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing`

## Dashboard
- `python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json`

## Local App Workflow
- `python3 tools/run_local_app_workflow.py --config examples/local_app_config.example.json --allow-missing`

## Show Local App Status
- `python3 tools/show_local_app_status.py --config examples/local_app_config.example.json`
