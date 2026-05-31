# Daily Workflow

## Morning
1. Run data collection
2. Run research analytics
3. Review signals

## Midday
1. Run paper simulator
2. Review trades

## Evening
1. Generate daily briefing
2. Run readiness audit
3. Review dashboard

## Research Insights Review (Phase 26)

After running research analytics, review the research insights to understand which strategies deserve further paper testing:

```bash
python3 tools/show_research_insights.py   --config examples/research_analytics_config.example.json   --allow-missing
```

This shows:
- Strategy comparison table with classification labels
- Top candidates for further paper testing
- Weak candidates to avoid for now
- Inconclusive items needing more data
- Data quality notes and warnings
- Next safe commands

You can also view it in the dashboard at: `http://127.0.0.1:8000/research-insights`

Research Insights is **local-only** and **paper-only / data-only**:
- No live trading
- No order submission
- Not financial advice
- Does not approve or enable live trading
- Does not guarantee performance
- Generated outputs are local and should not be committed

## One-Command Operator Flow (Phase 24)

For a simpler daily routine, use the operator day command:

```bash
python3 tools/run_operator_day.py   --config examples/local_app_config.example.json   --allow-missing
```

This single safe command orchestrates:
- Config validation
- Directory initialization
- Local app workflow
- Health bundle collection
- Readiness audit (if config available)
- Operator status summary

It is **paper-only / data-only**:
- No live trading
- No real-money order submission
- No broker calls
- No live network calls
- No credential input prompts
- No actual email send
- No actual Telegram send
- No cron installation
- No background service installation

The final summary shows:
- Workflow steps completed
- Readiness score and grade
- Briefing and dashboard status
- Warnings and blockers
- Next safe commands to open the dashboard

Generated reports, logs, and local outputs remain in `reports/` and should **not be committed**.

## Action Center (Phase 25)

For a focused view of what needs attention, use the action center:

```bash
python3 tools/show_action_center.py   --config examples/local_app_config.example.json   --allow-missing
```

The action center shows:
- Categorized warnings (config, data, safety, tests, docs)
- Critical blockers
- Action items per domain (readiness, workflow, briefing, dashboard)
- Latest generated outputs
- Next safe commands

You can also view it in the dashboard at: `http://127.0.0.1:8000/action-center`

## Commands

```bash
# Research insights
python3 tools/show_research_insights.py --config examples/research_analytics_config.example.json --allow-missing

# One-command operator day
python3 tools/run_operator_day.py --config examples/local_app_config.example.json --allow-missing

# Action center
python3 tools/show_action_center.py --config examples/local_app_config.example.json --allow-missing

# Data collection
python3 tools/run_data_collection.py --config examples/data_collection_config.example.json

# Research analytics
python3 tools/run_research_analytics.py --config examples/research_analytics_config.example.json

# Paper simulator
python3 tools/run_paper_simulator.py --config examples/paper_simulator_config.example.json

# Daily briefing
python3 tools/generate_daily_briefing.py --config examples/briefing_config.example.json

# Readiness audit
python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing

# Dashboard
python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json

# Show status
python3 tools/show_local_app_status.py --config examples/local_app_config.example.json
```
