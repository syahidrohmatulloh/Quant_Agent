#!/usr/bin/env python3
"""
Validate Phase 14 dashboard assets.
Checks imports, templates, no dangerous links/scripts, local-only safety.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PHASE14_MODULES = [
    "dashboard/__init__.py",
    "dashboard/app.py",
    "dashboard/routes.py",
    "dashboard/templates.py",
    "dashboard/static_assets.py",
    "dashboard/data_access.py",
    "dashboard/view_models.py",
    "dashboard/safety.py",
]

PHASE14_TOOLS = [
    "tools/run_dashboard_server.py",
    "tools/export_dashboard_static.py",
    "tools/validate_dashboard_assets.py",
]


def check_imports():
    errors = []
    try:
        from dashboard.app import create_phase14_app
        app = create_phase14_app()
        assert app is not None
    except Exception as e:
        errors.append(f"dashboard.app import failed: {e}")

    try:
        from dashboard.routes import router
        assert router is not None
    except Exception as e:
        errors.append(f"dashboard.routes import failed: {e}")

    try:
        from dashboard.templates import render_home
        assert render_home is not None
    except Exception as e:
        errors.append(f"dashboard.templates import failed: {e}")

    try:
        from dashboard.data_access import list_datasets
        assert list_datasets is not None
    except Exception as e:
        errors.append(f"dashboard.data_access import failed: {e}")

    try:
        from dashboard.safety import is_under_allowed_root
        assert is_under_allowed_root is not None
    except Exception as e:
        errors.append(f"dashboard.safety import failed: {e}")

    return errors


def check_templates_render():
    errors = []
    try:
        from dashboard.templates import render_home, render_datasets, render_reports
        from dashboard.view_models import HomeStatusViewModel, DatasetViewModel, ReportViewModel
        html = render_home(HomeStatusViewModel(0, 0, 0, None, None))
        assert "PAPER-ONLY" in html
        html = render_datasets([])
        assert "No datasets" in html
        html = render_reports([])
        assert "No reports" in html
    except Exception as e:
        errors.append(f"Template render check failed: {e}")
    return errors


def check_no_dangerous_links():
    errors = []
    from dashboard.static_assets import INLINE_CSS
    lowered = INLINE_CSS.lower()
    dangerous = ["<script", "javascript:", "eval(", "onclick="]
    for d in dangerous:
        if d in lowered:
            errors.append(f"INLINE_CSS contains dangerous content: {d}")
    return errors


def check_local_only_safety():
    errors = []
    server_path = PROJECT_ROOT / "tools" / "run_dashboard_server.py"
    if server_path.exists():
        content = server_path.read_text(encoding="utf-8")
        if 'default="127.0.0.1"' not in content:
            errors.append("run_dashboard_server.py does not default to 127.0.0.1")
    return errors


def check_no_live_trading_calls():
    errors = []
    forbidden = [
        "order" + chr(95) + "send",
        "execute" + chr(95) + "order",
        "place" + chr(95) + "order",
        "submit" + chr(95) + "order",
    ]
    for rel in PHASE14_MODULES + PHASE14_TOOLS:
        p = PROJECT_ROOT / rel
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8").lower()
        for f in forbidden:
            if f in content:
                errors.append(f"{rel} contains {f}")
    return errors


def check_no_credential_forms():
    errors = []
    forbidden = [
        'type="' + chr(112) + chr(97) + chr(115) + chr(115) + chr(119) + chr(111) + chr(114) + chr(100) + '"',
        "type='" + chr(112) + chr(97) + chr(115) + chr(115) + chr(119) + chr(111) + chr(114) + chr(100) + "'",
    ]
    for rel in PHASE14_MODULES + PHASE14_TOOLS:
        p = PROJECT_ROOT / rel
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8").lower()
        for f in forbidden:
            if f in content:
                errors.append(f"{rel} contains credential input: {f}")
    return errors


def check_no_external_cdn():
    errors = []
    from dashboard.static_assets import INLINE_CSS
    cdn_indicators = [
        "cdnjs.cloudflare.com", "unpkg.com", "jsdelivr.net",
        "bootstrapcdn.com", "googleapis.com", "jquery.com",
    ]
    lowered = INLINE_CSS.lower()
    for cdn in cdn_indicators:
        if cdn in lowered:
            errors.append(f"INLINE_CSS references external CDN: {cdn}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Phase 14 dashboard assets")
    args = parser.parse_args()

    all_errors = []
    all_errors.extend(check_imports())
    all_errors.extend(check_templates_render())
    all_errors.extend(check_no_dangerous_links())
    all_errors.extend(check_local_only_safety())
    all_errors.extend(check_no_live_trading_calls())
    all_errors.extend(check_no_credential_forms())
    all_errors.extend(check_no_external_cdn())

    if all_errors:
        print("VALIDATION FAILED:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All Phase 14 dashboard asset validations passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
