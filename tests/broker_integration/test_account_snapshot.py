"""Tests for account snapshot handling."""
from broker_integration.oanda.oanda_account_snapshot import build_oanda_snapshot
from broker_integration.alpaca.alpaca_account_snapshot import build_alpaca_snapshot
from broker_integration.ibkr.ibkr_account_snapshot import build_ibkr_snapshot


def test_snapshot_masks_account_id():
    snap = build_oanda_snapshot("1234567890", {"balance": 100000})
    assert "****7890" in snap["account_id_masked"]
    assert "1234567890" not in snap["account_id_masked"]


def test_snapshot_no_secrets():
    snap = build_alpaca_snapshot("ABC123", {"cash": 100000})
    for v in snap.values():
        assert "api_key" not in str(v).lower()
        assert "secret" not in str(v).lower()


def test_empty_positions_handled():
    snap = build_ibkr_snapshot("DU000000", {"balance": 100000, "positions": []})
    assert snap["open_positions"] == []
