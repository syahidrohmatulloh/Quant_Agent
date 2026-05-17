"""
Test experiment log (append-only JSONL).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import tempfile
from pathlib import Path
from experiment_manager.experiment_log import append_experiment_log, list_experiment_history


def test_experiment_log_append_only_jsonl():
    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = append_experiment_log(
            history_dir=tmpdir,
            run_id="run001",
            experiment_name="exp1",
            config_path="cfg.json",
            symbol_count=2,
            strategy_count=3,
            result_path="res.json",
            dashboard_json_path="dash.json",
        )
        assert Path(path1).exists()

        path2 = append_experiment_log(
            history_dir=tmpdir,
            run_id="run002",
            experiment_name="exp2",
            config_path="cfg2.json",
            symbol_count=1,
            strategy_count=2,
            result_path="res2.json",
            dashboard_json_path="dash2.json",
        )
        assert path1 == path2

        records = list_experiment_history(tmpdir)
        assert len(records) == 2
        assert records[0]["run_id"] == "run001"
        assert records[1]["run_id"] == "run002"
        assert records[0]["paper_only"] is True
        assert records[0]["no_order_submission"] is True
