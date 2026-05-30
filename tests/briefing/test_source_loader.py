"""Tests for source_loader.

Covers:
- load JSON
- load JSONL
- missing source with warning
- invalid JSON gracefully
"""

import json
import pytest
import tempfile
from pathlib import Path

from briefing.source_loader import load_json_source, load_jsonl_source, load_sources


def test_load_json_source():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "data.json"
        p.write_text(json.dumps({"key": "value"}))
        data = load_json_source(p)
        assert data["key"] == "value"


def test_load_jsonl_source():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "data.jsonl"
        p.write_text("\n".join([json.dumps({"a": 1}), json.dumps({"b": 2})]))
        data = load_jsonl_source(p)
        assert len(data) == 2
        assert data[0]["a"] == 1


def test_load_jsonl_skips_invalid_lines():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "data.jsonl"
        p.write_text("{\"a\": 1}\ninvalid json\n{\"b\": 2}")
        data = load_jsonl_source(p)
        assert len(data) == 2


def test_missing_source_with_allow_missing():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "missing.json"
        data = load_json_source(p, allow_missing=True)
        assert data is None


def test_missing_source_without_allow_missing_raises():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_json_source(p, allow_missing=False)


def test_invalid_json_with_allow_missing():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "bad.json"
        p.write_text("not json")
        data = load_json_source(p, allow_missing=True)
        assert data is None


def test_load_sources_missing_with_warning():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config = {
            "sources": {
                "exists": "exists.json",
                "missing": "missing.json",
            }
        }
        (root / "exists.json").write_text(json.dumps({"ok": True}))
        result = load_sources(config, root, allow_missing=True)
        assert result["sources"]["exists"] == {"ok": True}
        assert result["sources"]["missing"] is None
        assert any("missing" in w.lower() for w in result["warnings"])


def test_load_sources_rejects_path_traversal():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config = {
            "sources": {
                "bad": "../outside.json",
            }
        }
        result = load_sources(config, root, allow_missing=True)
        assert result["sources"]["bad"] is None
        assert any("escapes" in w.lower() for w in result["warnings"])
