# Broker Candidates for Indonesian Residents

## ⚠️ Disclaimer

This document is for **informational and planning purposes only**.
It does **not** constitute financial advice, broker recommendation, or live trading approval.
All integrations are **paper-only / demo-only**.

## Indonesia Local Brokers (BAPPEBTI)

Before using any local broker, verify their BAPPEBTI registration:
https://www.bappebti.go.id/id/regulasi/pialang_berjangka/

| Broker | BAPPEBTI | Demo | API | MT4 | MT5 | Integration Status |
|--------|----------|------|-----|-----|-----|---------------------|
| MIFX / Monex | Verify | Verify | Unknown | Verify | Verify | mt5_demo_possible |
| GKInvest | Verify | Verify | Unknown | Verify | Verify | mt5_demo_possible |
| HSB Investasi | Verify | Verify | Unknown | Verify | Verify | mt5_demo_possible |
| Finex | Verify | Verify | Unknown | Verify | Verify | mt5_demo_possible |
| Dupoin Futures | Verify | Unknown | Unknown | Unknown | Unknown | mock_only |
| Maxco Futures | Verify | Unknown | Unknown | Unknown | Unknown | mock_only |
| Octa Investama | Verify | Verify | Unknown | Verify | Verify | mt5_demo_possible |
| XTB Indonesia | Verify | Verify | Unknown | Verify | Verify | mt5_demo_possible |

**Why local brokers may be easier for KYC but harder for API:**
- KYC is local and regulated by BAPPEBTI.
- Most local brokers do not publish public REST APIs.
- Integration may be limited to MT4/MT5 demo read-only.

## Regional/Global Brokers

| Broker | Regulator | Indonesia Residents | Demo | API | MT4 | MT5 | Status |
|--------|-----------|---------------------|------|-----|-----|-----|--------|
| Interactive Brokers | SEC/FCA | Verify | Yes | Yes | No | No | api_possible |
| OANDA Singapore | MAS | Verify | Yes | Verify | Yes | Yes | api_possible |
| Alpaca | SEC | Verify | Yes | Yes | No | No | api_possible |
| Saxo | FSA | Verify | Yes | Verify | No | No | api_possible |
| IG | FCA/ASIC | Verify | Yes | Verify | Yes | No | api_possible |
| CMC Markets | FCA/ASIC | Verify | Yes | Verify | No | No | api_possible |
| Pepperstone | ASIC/FCA | Verify | Yes | Verify | Yes | Yes | mt5_demo_possible |
| FXCM | FCA | Verify | Yes | Verify | Yes | No | mt5_demo_possible |
| Exness | CySEC | Verify | Yes | No | Yes | Yes | mt5_demo_possible |
| XM | CySEC | Verify | Yes | No | Yes | Yes | mt5_demo_possible |
| FBS | IFC | Verify | Yes | No | Yes | Yes | mt5_demo_possible |
| Tickmill | FCA | Verify | Yes | No | Yes | Yes | mt5_demo_possible |

**Why regional brokers may be easier for API but require eligibility verification:**
- Many have documented REST APIs or SDKs.
- Indonesian resident eligibility varies by entity and changes over time.
- KYC may require additional documentation or be restricted.

## Recommended First Integration Path

1. **Start with mock adapters** for all brokers.
2. **Pick one broker** to verify manually:
   - For API development: **Interactive Brokers**, **OANDA**, or **Alpaca**.
   - For local compliance: **MIFX**, **GKInvest**, or **HSB** with MT5 demo.
3. **Open a demo account** and confirm market data quality.
4. **Run `tools/check_broker_connection.py`** with real credentials.
5. **Run `tools/run_live_data_paper_session.py`** for 100 cycles.
6. **Never enable live trading** until all safety checks pass and legal review is complete.

## Verification Checklist

- [ ] BAPPEBTI registration verified (for local brokers)
- [ ] Broker entity page checked for Indonesia eligibility
- [ ] Demo account opened and functional
- [ ] API credentials generated (if available)
- [ ] `check_broker_connection.py` returns healthy
- [ ] `run_live_data_paper_session.py` completes 100 cycles
- [ ] Reconciliation shows matched or minor warnings only
- [ ] No `LIVE_TRADING_ENABLED=true` in environment
- [ ] `allow_live_orders` remains `false`
