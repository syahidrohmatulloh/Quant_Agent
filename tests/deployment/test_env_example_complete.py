
import os
import pytest

def test_env_example_exists():
    assert os.path.exists(".env.example")

def test_env_example_contains_required_vars():
    with open(".env.example", "r") as f:
        content = f.read()
    required = ["QUANT_MODE", "QUANT_BROKER", "QUANT_SQLITE_PATH", "AUDIT_JSONL_PATH"]
    for var in required:
        assert var in content, f"Missing {var} in .env.example"

def test_env_example_paper_default():
    with open(".env.example", "r") as f:
        content = f.read()
    assert "QUANT_MODE=paper" in content or "paper" in content.lower()
