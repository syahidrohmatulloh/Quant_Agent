# Safety and Limitations

> **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission. Not financial advice. This system does not guarantee performance.

## Core Safety Principles

1. **Quant_Agent is paper-only.** All trading decisions are simulated. No real money is at risk.
2. **No real order submission.** The system does not send orders to brokers.
3. **No profitability guarantee.** Past simulated performance does not predict future results.
4. **Not financial advice.** This is a research tool, not an investment recommendation.
5. **Readiness gate is not live approval.** Passing the readiness audit does not authorize live trading.

## Known Limitations

### MetaTrader5 on macOS
The `MetaTrader5` pip package is not available on macOS. Use the CSV workflow instead:
- Export data from MT5 as CSV
- Import via `tools/import_csv_market_data.py`

### CSV Data Quality
- Simulated results depend on CSV data quality.
- Missing timestamps, gaps, or bad ticks will affect signals.
- Always validate data with `tools/validate_market_data.py` before running experiments.

### Simulator Costs
- Transaction costs in the simulator are approximate.
- Slippage is modeled but may not match real market conditions.
- Spread assumptions are static unless configured otherwise.

### Research Analytics
- All analytics are historical simulation only.
- Sharpe ratio, drawdown, and attribution are based on simulated fills.
- No forward-testing or out-of-sample validation is performed automatically.

## Credential Safety

- **Never commit credentials to the repo.**
- Use `local_configs/` for real configs (gitignored).
- Example configs in `examples/` contain placeholders only.
- If you accidentally commit a secret, rotate it immediately.

## Before Any Future Live Discussion

Live trading would require ALL of the following, separately and explicitly:

1. **Separate design review** — Architecture must be reviewed for live suitability.
2. **Legal/compliance review** — Ensure regulatory compliance in your jurisdiction.
3. **Security review** — Audit secrets management, access controls, and encryption.
4. **Broker sandbox testing** — Test with paper money on broker sandbox environment.
5. **Risk kill-switch** — Implement automatic position flattening on error.
6. **Manual approval** — Human sign-off before any live execution.
7. **Independent validation** — Third-party review of logic and risk controls.

Until all of the above are completed, Quant_Agent remains strictly paper-only.
