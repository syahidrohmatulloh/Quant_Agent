# Quant Platform v3

Event-driven backtester + paper trading foundation.

## Phases
- 1.5/2.5: SQLite, audit, auth, paper broker, risk, CLI tools
- 3: Event-driven backtester, execution simulator, performance metrics, walk-forward testing

## Run Tests
```bash
python -m pytest tests/ -v
```

## Run Backtest
```bash
python tools/run_backtest.py --config backtest_config.json --data historical_data.json --output reports/
```


**Phase 3 test suite passed locally/sandbox: 75 passed.**


## Phase 4 — Research Pipeline + Model Governance

**Status:** Complete  
**Test suite passed locally/sandbox: 107 passed (75 baseline + 32 new).**

### New Modules
- `research_pipeline/` — DatasetBuilder, FeatureRegistry, FeatureEngineering, LabelBuilder, TrainTestSplit, ModelTrainer, ModelEvaluator, ModelRegistry, ModelGovernance, DriftMonitor, ExperimentTracker
- `model_governance/` — ApprovalWorkflow, ModelCard, ChampionChallenger, Rollback
- `tests/research/` — 32 new tests covering dataset building, features, labels, splits, registry, governance, drift
- `tools/` — build_dataset.py, train_model.py, evaluate_model.py, register_model.py, approve_model.py, check_drift.py

### Key Design Decisions
- No live trading automation added.
- Only `approved` models can generate systematic signals.
- Simple rule-based mock model used when sklearn unavailable.
- Time-series splits only — no random shuffle.
- Triple-barrier labels supported with explicit horizon.
- Feature drift alerts at 3-sigma threshold.


## Phase 5 — Portfolio Optimization + Live Signal Bridge (Paper-Only)

**Status:** Complete  
**Test suite passed locally/sandbox: 178 passed (107 baseline + 71 new).**  
**Mode:** Paper-only. No live trading enabled.

### New Modules
- `portfolio_optimization/` — CovarianceEstimator, CorrelationAnalyzer, VolatilityTargeting, RiskParityAllocator, HRPAllocator, AllocationEngine, Constraints, RebalanceEngine
- `signal_bridge/` — ApprovedModelLoader, FeatureRuntime, PredictionService, SignalGenerator, SignalRouter, PaperSignalExecutor
- `monitoring/` — LiveMetrics, Alerting, SignalMonitor, PortfolioMonitor
- `tests/portfolio/` — 24 tests
- `tests/signal_bridge/` — 22 tests
- `tests/monitoring/` — 16 tests
- `tools/` — run_signal_bridge.py, generate_paper_signal.py, run_portfolio_allocation.py, monitor_paper_signals.py

### Key Design Decisions
- Only `approved` models can generate signals. Draft/candidate/rejected/archived are blocked.
- Signal bridge routes exclusively to paper broker. No live broker calls.
- Circuit breaker and rate limiting protect the system.
- Every signal is audited: signal_generated → signal_routed_to_paper → paper_order_created.
- Portfolio allocation respects max weight, gross/net exposure, leverage, and correlation caps.
- Volatility targeting reduces exposure when realized vol exceeds target.
- Rebalance engine avoids churn via minimum trade threshold.
- Monitoring generates alerts for rejection spikes, drawdown, drift, circuit breaker, missing features.


## Phase 6 — Live Data, Scheduler, Dashboard, Persistence, Deployment

**Status:** Complete  
**Test suite passed locally/sandbox: 256 passed (178 baseline + 78 new).**  
**Mode:** Paper-only. No live trading enabled.

### New Modules
- `live_data/` — BaseMarketDataAdapter, DataNormalizer, DataQualityMonitor, MarketClock, CSVReplayAdapter, PollingAdapter, MT5PriceAdapter
- `scheduler/` — TaskScheduler, SignalLoop, RetryPolicy, Heartbeat, JobStore
- `dashboard/` — FastAPI HTML dashboard (positions, signals, alerts, models, backtests) with auth
- `persistence/` — ConnectionManager, Repository, SQLiteBackend, PostgresBackend, MigrationRunner
- `deployment/` — Dockerfile, docker-compose.yml, entrypoint.sh, healthcheck.sh
- `ops/` — Runbook, incident response, paper trading checklist, backup/restore guide
- `tests/live_data/` — 24 tests
- `tests/scheduler/` — 15 tests
- `tests/dashboard/` — 13 tests
- `tests/persistence/` — 9 tests
- `tests/deployment/` — 5 tests
- `tools/` — run_scheduler.py, run_signal_loop_once.py, replay_market_data.py, check_system_health.py, export_dashboard_snapshot.py, backup_data.py, restore_data.py

### Key Design Decisions
- Data normalizer validates and standardizes all incoming ticks/bars.
- Data quality monitor detects stale data, wide spreads, backwards timestamps, duplicate bars.
- Market clock respects FX weekend (Fri 22:00 UTC – Sun 22:00 UTC).
- Signal loop is gated by: circuit breaker → market clock → data quality → model approval → feature runtime → confidence → paper execution.
- Dashboard is auth-protected (viewer token). No secrets exposed in HTML.
- Persistence layer supports SQLite (default) and PostgreSQL (optional, commented in docker-compose).
- Migrations are idempotent and versioned.
- Docker image defaults to paper mode. No secrets baked into image.
- All 256 tests pass.

### Deployment

```bash
cd deployment
docker-compose up --build
```

Access dashboard at http://localhost:8000/dashboard/
