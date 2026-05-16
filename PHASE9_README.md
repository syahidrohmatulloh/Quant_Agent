# Phase 9: Real Broker Transport + Streaming

## ⚠️ PAPER-ONLY WARNING

**This phase is strictly paper-only. No live trading is enabled.**
All broker adapters default to paper/practice/demo environments.
Live trading endpoints are explicitly rejected.

## What Phase 9 Adds

1. **HTTP Transport Layer** — Real HTTP transport with retry, rate-limit, auth, and credential redaction
2. **Mock Transport** — Deterministic mock HTTP transport for testing without network
3. **OANDA Practice HTTP Transport** — Real OANDA v3 REST API transport with safety gates
4. **OANDA Practice Order Client** — Paper-only order submission with dry-run default
5. **OANDA Practice Snapshot** — Real account snapshot fetching with masked account IDs
6. **OANDA Practice Streaming/Polling** — Polling-based market data stream
7. **Streaming Layer** — Generic stream events, health, reconnect, supervisor, recorder
8. **CLI Tools** — 6 new tools for diagnostics, streaming, snapshot, dry-run order, safety validation
9. **Dashboard Extension** — Stream, snapshot, and safety dashboard pages

## Architecture

```
broker_integration/transport/
  ├── http_transport.py      # Real HTTP with retry/rate-limit/auth
  ├── mock_transport.py      # Deterministic mock for tests
  ├── auth.py                # Env-only credential reading
  ├── redaction.py           # Credential masking
  ├── retry_policy.py        # Exponential backoff
  ├── rate_limit.py          # Request rate limiting
  └── network_errors.py      # Transport error hierarchy

broker_integration/oanda/
  ├── oanda_http_transport.py       # OANDA v3 REST client
  ├── oanda_practice_orders.py      # Paper-only order client
  ├── oanda_practice_snapshot.py    # Account snapshot fetcher
  ├── oanda_streaming.py            # Polling stream
  ├── oanda_instruments.py          # Symbol normalization
  ├── oanda_rate_limit.py           # OANDA-specific rate limiter
  └── oanda_errors.py               # OANDA error classes

streaming/
  ├── stream_event.py         # Event dataclasses
  ├── stream_health.py        # Stream health monitoring
  ├── stream_reconnect.py     # Reconnect policy
  ├── stream_supervisor.py    # Stream supervisor
  ├── stream_recorder.py      # Durable stream output
  ├── polling_stream.py       # Generic polling stream
  └── market_data_stream.py   # Abstract stream interface
```

## Safety Gates

| Gate | Implementation | Default |
|------|---------------|---------|
| Live environment rejected | `BrokerConfig.validate()` | Rejects "live", "production", "real" |
| Live orders rejected | `BrokerConfig.validate()` | Rejects `allow_live_orders=True` |
| Live endpoint rejected | `OandaHttpTransport._validate_safety()` | Rejects URLs containing "api-fxtrade" |
| Order submission disabled | `allow_order_submission=False` | Must be explicitly enabled |
| Dry-run default | `dry_run=True` in order client | Must be explicitly disabled |
| Credentials redacted | `redaction.py` | Never exposed in logs/repr |
| Account ID masked | `mask_account_id()` | Last 4 chars only |

## How to Configure OANDA Practice

1. Create OANDA practice account: https://www.oanda.com/
2. Generate practice API key
3. Set environment variables:
   ```bash
   export OANDA_API_KEY="your-practice-key"
   export OANDA_ACCOUNT_ID="your-practice-account-id"
   ```
4. Use config: `examples/oanda_practice_real_config.example.json`

## CLI Tools

### Diagnose OANDA Connection
```bash
python tools/diagnose_oanda_practice.py \
  --config examples/oanda_practice_real_config.example.json
```

### Stream OANDA Prices
```bash
python tools/stream_oanda_prices.py \
  --config examples/oanda_practice_real_config.example.json \
  --symbol EUR_USD \
  --max-events 100 \
  --output reports/oanda_stream/
```

### Collect Market Data (Multiple Symbols)
```bash
python tools/collect_oanda_market_data.py \
  --config examples/oanda_practice_real_config.example.json \
  --symbols EUR_USD GBP_USD USD_JPY \
  --poll-interval 5 \
  --duration-seconds 300 \
  --output reports/oanda_collection/
```

### Fetch Account Snapshot
```bash
python tools/fetch_oanda_practice_snapshot.py \
  --config examples/oanda_practice_real_config.example.json \
  --output reports/snapshot.json
```

### Dry-Run Paper Order
```bash
python tools/dry_run_oanda_paper_order.py \
  --config examples/oanda_practice_real_config.example.json \
  --symbol EUR_USD \
  --units 1000 \
  --side buy \
  --dry-run \
  --model-id model-001 \
  --signal-id signal-001
```

### Validate Safety
```bash
python tools/validate_phase9_safety.py \
  --config examples/oanda_practice_real_config.example.json
```

## Mock Transport for Testing

```python
from broker_integration.transport.mock_transport import MockTransport

mock = MockTransport()
mock.enqueue_response({"accounts": [{"id": "001"}]})
result = mock.get("/v3/accounts")
assert result["accounts"][0]["id"] == "001"
assert mock.requests[0]["method"] == "GET"
```

## Streaming Usage

```python
from broker_integration.broker_config import BrokerConfig
from broker_integration.oanda.oanda_streaming import OandaPollingStream

config = BrokerConfig(
    broker_name="oanda",
    environment="practice",
    api_key_env="OANDA_API_KEY",
    account_id_env="OANDA_ACCOUNT_ID",
)
stream = OandaPollingStream(config, poll_interval_seconds=5.0, max_events=10)
for event in stream.start("EUR_USD"):
    print(event)
stream.stop()
```

## Test Count

- Phase 9 adds ~55 new tests.
- Target total: 340+ tests (286 baseline + 55 new).
- **Tests not executed against the real GitHub baseline** — designed to be compatible.

## Known Limitations

1. OANDA transport is mock-first unless real credentials and `--real-network` flag are provided.
2. Streaming is polling-based, not WebSocket.
3. Only OANDA has real transport implementation; Alpaca and IBKR remain mock-only in Phase 9.
4. No real order submission by default — `dry_run=True` and `allow_order_submission=False`.
5. Dashboard extension is additive — must be registered manually in main FastAPI app.

## Recommended Next Step (Phase 10)

- Implement WebSocket streaming adapter for OANDA.
- Add Alpaca real HTTP transport.
- Add IBKR TWS/Gateway transport.
- Implement real-time order book depth normalization.
- Add streaming P&L reconciliation.
