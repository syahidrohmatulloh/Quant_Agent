# Phase History

> **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission. Not financial advice.

## Development Timeline

| Phase | Name | Purpose | Major Deliverables | Safety Notes | Tag |
|-------|------|---------|---------------------|--------------|-----|
| 6 | Baseline | Core architecture and tests | Modular structure, pytest suite | Paper-only foundation | phase-6-clean |
| 7 | Runtime Validation | Safety checks and validation | Runtime gate, config validation | No live execution | phase-7-clean |
| 8 | Broker Integration | Broker adapter design | Paper-only broker adapters | Adapters are mock/paper | phase-8-clean |
| 9 | OANDA Practice | Transport and streaming | OANDA practice transport, dry-run safety | Practice account only, no live | phase-9-clean |
| 10 | Strategy Library | Institutional-style strategies | Signal library, backtest framework | Signals are simulated | phase-10-clean |
| 11 | MT5 Integration | Market data from MT5 | CSV import, MT5 data bridge | CSV-only, no live MT5 API | phase-11-clean |
| 12 | CSV Workflow | Real market data runtime | CSV signal, CSV backtest | Historical data only | phase-12-clean |
| 13 | Experiment Manager | Parameter sweeps | Experiment tracking, comparison | Simulated experiments | phase-13-clean |
| 14 | Local Dashboard | Quant UI | Local web dashboard | Read-only, localhost only | phase-14-clean |
| 15 | Paper Orchestration | Paper trading workflow | Decision engine, paper config | Paper decisions only | phase-15-clean |
| 16 | Data Manager | Dataset import and versioning | Import tools, dataset manager | CSV data only | phase-16-clean |
| 17 | Research Analytics | Performance attribution | Analytics engine, reports | Historical simulation only | phase-17-clean |
| 18 | Paper Simulator v2 | Portfolio simulation | Simulator v2, risk controls | Simulated fills only | phase-18-clean |
| 19 | Alerting & Briefing | Daily reports | Briefing generator, alerts | Text-only, no auto-send | phase-19-clean |
| 20 | Local App Packaging | One-command launcher | Launcher, init tools, cleanup | Local-only, no background service | phase-20-clean |
| 21 | Readiness Gate | Safety audit | Audit engine, scoring, reports | Explicitly not live approval | phase-21-clean |
| 22 | Documentation | User manual and demo | README, docs, validation tools | Paper-only documentation | phase-22-clean |

## Test Count Evolution

| Phase | Tests Passed |
|-------|-------------|
| 6 | Baseline |
| 7 | + runtime validation |
| 8 | + broker adapters |
| 9 | + OANDA transport |
| 10 | + strategy library |
| 11 | + MT5 integration |
| 12 | + CSV workflow |
| 13 | + experiment manager |
| 14 | + dashboard |
| 15 | + paper orchestration |
| 16 | + data manager |
| 17 | + research analytics |
| 18 | + paper simulator |
| 19 | + briefing |
| 20 | + local app |
| 21 | + readiness gate |
| 22 | + documentation |

## Safety Evolution

Each phase added safety checks:
- Phase 7: Runtime validation
- Phase 9: Dry-run safety for OANDA
- Phase 15: Paper-only orchestration
- Phase 18: Simulator risk controls
- Phase 19: No auto-send for alerts
- Phase 20: Cleanup requires confirmation
- Phase 21: Full readiness gate with scoring
- Phase 22: Documentation safety validation

## Disclaimer

Performance metrics shown in any phase are simulated and historical. They do not guarantee future results.
