import os
import sys
import json
import pytest
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.paper_session import PaperSessionRunner, run_paper_session


class TestPaperSessionRunner:
    def _make_replay_csv(self, path: str, rows: int = 10):
        with open(path, "w") as f:
            f.write("timestamp,bid,ask,symbol\n")
            for i in range(rows):
                f.write(f"2024-01-01T00:{i:02d}:00+00:00,1.100{i%10},1.100{i%10+1},EURUSD\n")

    def _make_config(self, model_status: str = "approved"):
        return {
            "model": {
                "model_id": "test-model-001",
                "model_version": "v1",
                "dataset_id": "ds-001",
                "feature_set_id": "sma_v1",
                "label_config": {"horizon": 10},
                "training_period": "2023-01-01/2023-06-01",
                "validation_period": "2023-06-01/2023-09-01",
                "test_period": "2023-09-01/2023-12-01",
                "metrics": {"accuracy": 0.55},
                "artifact_path": "",
                "approval_status": model_status,
                "approved_by": "test",
                "approval_notes": ""
            },
            "starting_balance": 50000.0,
            "symbols": ["EURUSD"],
            "timeframe": "1m",
            "min_confidence": 0.5
        }

    def test_session_runs_n_cycles_deterministically(self):
        with tempfile.TemporaryDirectory() as td:
            replay = os.path.join(td, "replay.csv")
            self._make_replay_csv(replay, rows=20)
            config_path = os.path.join(td, "config.json")
            with open(config_path, "w") as f:
                json.dump(self._make_config(), f)
            out_dir = os.path.join(td, "session_001")
            result = run_paper_session(replay, config_path, cycles=10, output_dir=out_dir)
            assert result["cycles_run"] == 10
            assert result["paper_only"] is True

    def test_outputs_are_created(self):
        with tempfile.TemporaryDirectory() as td:
            replay = os.path.join(td, "replay.csv")
            self._make_replay_csv(replay, rows=20)
            config_path = os.path.join(td, "config.json")
            with open(config_path, "w") as f:
                json.dump(self._make_config(), f)
            out_dir = os.path.join(td, "session_001")
            run_paper_session(replay, config_path, cycles=5, output_dir=out_dir)
            assert os.path.exists(os.path.join(out_dir, "session_summary.json"))
            assert os.path.exists(os.path.join(out_dir, "audit_validation.json"))
            assert os.path.exists(os.path.join(out_dir, "alerts.json"))

    def test_unapproved_model_blocks_signals(self):
        with tempfile.TemporaryDirectory() as td:
            replay = os.path.join(td, "replay.csv")
            self._make_replay_csv(replay, rows=20)
            config_path = os.path.join(td, "config.json")
            with open(config_path, "w") as f:
                json.dump(self._make_config(model_status="draft"), f)
            out_dir = os.path.join(td, "session_001")
            result = run_paper_session(replay, config_path, cycles=5, output_dir=out_dir)
            # All signals should be rejected because model is not approved
            assert result["signals_generated"] == 0
            assert result["signals_rejected"] > 0

    def test_stale_data_creates_rejection(self):
        with tempfile.TemporaryDirectory() as td:
            replay = os.path.join(td, "replay.csv")
            # Write old timestamps
            with open(replay, "w") as f:
                f.write("timestamp,bid,ask,symbol\n")
                f.write("2020-01-01T00:00:00+00:00,1.1000,1.1001,EURUSD\n")
                f.write("2020-01-01T00:01:00+00:00,1.1002,1.1003,EURUSD\n")
            config_path = os.path.join(td, "config.json")
            with open(config_path, "w") as f:
                json.dump(self._make_config(), f)
            out_dir = os.path.join(td, "session_001")
            result = run_paper_session(replay, config_path, cycles=2, output_dir=out_dir)
            # Should have rejections due to stale data
            assert result["signals_rejected"] > 0

    def test_audit_validation_passes(self):
        with tempfile.TemporaryDirectory() as td:
            replay = os.path.join(td, "replay.csv")
            self._make_replay_csv(replay, rows=20)
            config_path = os.path.join(td, "config.json")
            with open(config_path, "w") as f:
                json.dump(self._make_config(), f)
            out_dir = os.path.join(td, "session_001")
            run_paper_session(replay, config_path, cycles=5, output_dir=out_dir)
            audit_val_path = os.path.join(out_dir, "audit_validation.json")
            assert os.path.exists(audit_val_path)
            with open(audit_val_path) as f:
                val = json.load(f)
            assert val["valid"] is True

    def test_no_live_order_execution_occurs(self):
        with tempfile.TemporaryDirectory() as td:
            replay = os.path.join(td, "replay.csv")
            self._make_replay_csv(replay, rows=20)
            config_path = os.path.join(td, "config.json")
            with open(config_path, "w") as f:
                json.dump(self._make_config(), f)
            out_dir = os.path.join(td, "session_001")
            result = run_paper_session(replay, config_path, cycles=5, output_dir=out_dir)
            assert result["paper_only"] is True
            # No live broker orders
            audit_path = os.path.join(out_dir, "audit.jsonl")
            if os.path.exists(audit_path):
                with open(audit_path) as f:
                    for line in f:
                        ev = json.loads(line)
                        assert "live" not in ev.get("event_type", ""), f"Live event found: {ev}"
