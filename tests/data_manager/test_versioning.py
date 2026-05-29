"""Tests for Versioning."""
import tempfile
from pathlib import Path

import pytest

from data_manager.versioning import Versioning


def test_versioning_lists_versions():
    with tempfile.TemporaryDirectory() as td:
        v = Versioning(Path(td) / "versions")
        dataset = Path(td) / "market" / "EURUSD_H1.csv"
        dataset.parent.mkdir(parents=True, exist_ok=True)
        lines = ["timestamp,open", "2024-01-01T00:00:00,1.0"]
        dataset.write_text("\n".join(lines))
        v.backup(dataset)
        versions = v.list_versions(dataset)
        assert len(versions) >= 1


def test_restore_requires_confirm_restore():
    with tempfile.TemporaryDirectory() as td:
        v = Versioning(Path(td) / "versions")
        dataset = Path(td) / "market" / "EURUSD_H1.csv"
        dataset.parent.mkdir(parents=True, exist_ok=True)
        lines = ["timestamp,open", "2024-01-01T00:00:00,1.0"]
        dataset.write_text("\n".join(lines))
        bp = v.backup(dataset)
        lines2 = ["timestamp,open", "2024-01-01T00:00:00,2.0"]
        dataset.write_text("\n".join(lines2))
        with pytest.raises(ValueError):
            v.restore(dataset, bp, confirm=False)
