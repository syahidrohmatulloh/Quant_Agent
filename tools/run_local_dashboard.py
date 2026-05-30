#!/usr/bin/env python3
"""CLI: Run local dashboard server wrapper.

Default host 127.0.0.1. Rejects 0.0.0.0 unless explicit --allow-nonlocal-host.
Prints URL only. Does not auto-open browser unless configured.
No external CDN.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse

from local_app.app_config import load_config
from local_app.safety import print_disclaimer


def main():
    parser = argparse.ArgumentParser(description="Run local dashboard server")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--allow-nonlocal-host", action="store_true", help="Allow non-local host binding")
    args = parser.parse_args()

    print_disclaimer()
    print()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"FAIL: Config file not found: {config_path}")
        sys.exit(1)

    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"FAIL: Could not load config: {e}")
        sys.exit(1)

    dashboard_cfg = config.get("dashboard", {})
    host = args.host or dashboard_cfg.get("host", "127.0.0.1")
    port = args.port or dashboard_cfg.get("port", 8000)
    auto_open = dashboard_cfg.get("auto_open_browser", False)

    if host == "0.0.0.0" and not args.allow_nonlocal_host:
        print("ERROR: dashboard.host = 0.0.0.0 rejected. Use --allow-nonlocal-host to override.")
        sys.exit(1)

    print(f"Dashboard URL: http://{host}:{port}")
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    if auto_open:
        print("Auto-open browser is enabled in config (not implemented in wrapper).")
    else:
        print("Auto-open browser is disabled.")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    # Delegate to Phase 14 dashboard server
    try:
        import uvicorn
        uvicorn.run("dashboard.app:app", host=host, port=port, reload=False)
    except ImportError:
        print("Error: uvicorn is required. Install with: pip install uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()
