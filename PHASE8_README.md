# Phase 8: Live Data Paper Broker Integration

## ⚠️ PAPER-ONLY WARNING

**This phase is strictly paper-only. No live trading is enabled.**
All broker adapters default to paper/practice/demo environments.
Live trading endpoints are explicitly rejected.

## What Phase 8 Adds

1. **Broker Integration Framework** — Abstract base adapters for connecting to broker paper/demo accounts
2. **Real Market Data Adapters** — OANDA practice, Alpaca paper, IBKR paper interfaces
3. **Account Snapshot Reconciliation** — Compare internal paper state with broker paper snapshot
4. **Live Paper Session Runner** — Run paper trading cycles using live/polled broker market data
5. **Session Supervisor** — Track uptime, failures, reconnect policy, heartbeat
6. **Runtime Recorder** — Persist ticks, signals, rejections, snapshots, reconciliation results
7. **Broker Health Diagnostics** — CLI tools to check connectivity without real orders
8. **Indonesian & Regional Broker Catalog** — Metadata for BAPPEBTI-listed and regional brokers
9. **Dashboard Extension** — Additive broker/live-paper/reconciliation pages

## Supported Broker Adapters

| Broker | Environment | Market Data | Account Snapshot | Paper Orders | Status |
|--------|-------------|-------------|------------------|--------------|--------|
| OANDA | practice | mock + API interface | mock + API interface | internal paper only | api_possible |
| Alpaca | paper | mock + API interface | mock + API interface | internal paper only | api_possible |
| IBKR | paper | mock + API interface | mock + API interface | internal paper only | api_possible |

All adapters use **optional imports** — if `requests` or `ib_insync` is missing, they return `dependency_missing` health status.

## How to Configure OANDA Practice

1. Create an OANDA practice account at https://www.oanda.com/
2. Generate a practice API key
3. Set environment variables:
   ```bash
   export OANDA_API_KEY="your-practice-key"
   export OANDA_ACCOUNT_ID="your-practice-account"
   ```
4. Use the example config: `examples/oanda_practice_config.example.json`

## How to Configure Alpaca Paper

1. Create an Alpaca paper account at https://alpaca.markets/
2. Generate paper API credentials
3. Set environment variables:
   ```bash
   export ALPACA_API_KEY="your-paper-key"
   export ALPACA_API_SECRET="your-paper-secret"
   ```
4. Use the example config: `examples/alpaca_paper_config.example.json`

## How to Run Broker Connection Diagnostics

```bash
python tools/check_broker_connection.py \
  --config examples/oanda_practice_config.example.json
```

Expected output (without credentials):
```json
{
  "broker": "oanda",
  "environment": "practice",
  "healthy": false,
  "reason": "missing_credentials",
  "paper_only": true
}
```

## How to Run Live Data Paper Session

```bash
python tools/run_live_data_paper_session.py \
  --config examples/live_paper_session_config.example.json \
  --cycles 100 \
  --output reports/live_session_001/
```

## How to Reconcile Paper Broker Snapshot

```bash
python tools/fetch_broker_snapshot.py \
  --config examples/oanda_practice_config.example.json \
  --output reports/snapshot.json

python tools/reconcile_paper_broker.py \
  --internal reports/live_session_001/session_summary.json \
  --broker reports/snapshot.json \
  --output reports/reconciliation.json
```

## How to Verify No Live Trading is Enabled

1. Check `BrokerConfig.validate()` — it rejects `environment: live`
2. Check `LIVE_TRADING_ENABLED` env var — if set to `true`, Phase 8 tools fail closed
3. Check `allow_live_orders` — defaults to `false`, cannot be set to `true`
4. Check adapter `live_trading_enabled` property — always returns `False`
5. Check `submit_paper_order` — only submits to internal paper broker, never to live broker

## Known Limitations

- All broker adapters are **mock-first** with optional real API transport.
- No real network calls are made unless credentials are configured and transport is injected.
- Indonesian local brokers are **catalog-only** or **MT5 demo read-only** — no REST API integration.
- Regional broker availability for Indonesian residents must be **manually verified**.
- Dashboard extension is **additive** — must be registered manually in main app.

## Test Count

- Phase 8 adds ~60 new tests.
- Target total: 340+ tests (286 baseline + 60 new).
- **Tests not executed against the real GitHub baseline** — they are written to be compatible with the existing architecture.

## Recommended Next Step (Phase 9)

- Implement real transport for one broker (OANDA or Alpaca) with actual API calls in a sandbox.
- Add WebSocket/streaming market data adapter.
- Add order book depth normalization.
- Implement real-time P&L reconciliation.
