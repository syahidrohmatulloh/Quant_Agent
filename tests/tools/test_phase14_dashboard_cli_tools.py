"""
Test Phase 14 dashboard CLI tools.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import subprocess
import tempfile
from pathlib import Path

PHASE14_TOOLS = [
    "run_dashboard_server.py",
    "export_dashboard_static.py",
    "validate_dashboard_assets.py",
]


def _run_tool(script_name, args):
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools", script_name)
    cmd = [sys.executable, script] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def test_run_dashboard_server_help():
    result = _run_tool("run_dashboard_server.py", ["--help"])
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "127.0.0.1" in result.stdout or "host" in result.stdout.lower()


def test_export_dashboard_static_writes_html():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "static", "index.html")
        result = _run_tool("export_dashboard_static.py", ["--output", out_path, "--project-root", tmpdir])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert os.path.exists(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "PAPER-ONLY" in content
        assert "DATA-ONLY" in content


def test_validate_dashboard_assets_passes():
    result = _run_tool("validate_dashboard_assets.py", [])
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "passed" in result.stdout.lower() or "All" in result.stdout


def test_cli_tools_no_broker_credentials():
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools")
    forbidden = [
        "order" + "_send",
        "execute" + "_order",
        "place" + "_order",
        "submit" + "_order",
    ]
    for fname in PHASE14_TOOLS:
        with open(os.path.join(tools_dir, fname), "r", encoding="utf-8") as f:
            content = f.read()
        for f in forbidden:
            assert f not in content, f"{fname} contains {f}"


def test_cli_tools_no_live_network():
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools")
    for fname in PHASE14_TOOLS:
        with open(os.path.join(tools_dir, fname), "r", encoding="utf-8") as f:
            content = f.read()
        assert "urllib" not in content, f"{fname} uses urllib"
        assert "requests" not in content, f"{fname} uses requests"
        assert "socket" not in content, f"{fname} uses socket"
