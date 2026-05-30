# Post-MVP Roadmap

> **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission. Not financial advice.

## Overview

These future phases are optional and remain paper-only unless separately and explicitly approved. They are suggestions for extending the Quant_Agent research framework.

## Proposed Phases

### Phase 23: Readiness Warning Cleanup
- Reduce readiness audit warnings to zero
- Improve safety score to A+ consistently
- Add more granular audit checks
- **Safety:** Still paper-only. Does not enable live trading.

### Phase 24: Data Ingestion Refinement
- Better CSV validation and error handling
- Dataset governance and versioning
- Data quality scoring
- **Safety:** CSV-only. No live market data feeds.

### Phase 25: Strategy Research Notebooks
- Jupyter notebook templates for strategy research
- Automated report pack generation
- PDF export for strategy documentation
- **Safety:** Research only. No execution.

### Phase 26: Paper Trading Dashboard v2
- Enhanced UI with more charts
- Historical simulation replay
- Better exposure visualization
- **Safety:** Read-only dashboard. No order submission.

### Phase 27: Broker Sandbox Abstraction Review
- Review broker adapter design for sandbox use
- Abstract paper vs. sandbox vs. live layers
- Document sandbox testing procedures
- **Safety:** Sandbox only. No live execution.

### Phase 28: Security and Secrets Management Design
- Design secrets management architecture
- Key rotation procedures
- Access control design
- **Safety:** Design only. No implementation of live trading.

### Phase 29: Compliance-Style Runbook
- Operational runbook for paper trading
- Incident response procedures
- Change management process
- **Safety:** Documentation only.

### Phase 30: Optional Cloud Deployment
- Read-only dashboard deployment for demo
- No trading logic in cloud
- Static report hosting
- **Safety:** Read-only. No execution. No credentials in deployment.

## Important Notes

- All phases above are **optional**.
- The project remains **paper-only** unless a separate, explicit approval process is completed.
- No phase in this roadmap enables live trading by default.
- Live trading would require: design review, legal/compliance review, security audit, broker sandbox testing, risk kill-switch, manual approval, and independent validation.

## Current Status

- Phase 22 (Documentation) is complete.
- The system is ready for paper-only research and demonstration.
- Future work should prioritize safety and documentation over live features.
