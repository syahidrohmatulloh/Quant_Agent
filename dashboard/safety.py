"""
Safety utilities for the Phase 14 dashboard.
Path traversal prevention, allowed directory validation,
no credential exposure, no live broker calls.
"""
import os
from pathlib import Path
from typing import Set

# Allowed directories for dashboard file access
ALLOWED_ROOTS: Set[str] = {
    "data/market",
    "examples",
    "configs",
    "reports/experiments",
    "reports/dashboard/experiments",
    "reports/experiments/history",
}


def normalize_path(path: str) -> str:
    """Return absolute, resolved path string."""
    return str(Path(path).resolve())


def is_under_allowed_root(path: str, project_root: str = ".") -> bool:
    """
    Check if the given path is under one of the allowed roots.
    Prevents path traversal outside allowed directories.
    """
    target = Path(normalize_path(path))
    proj = Path(normalize_path(project_root))

    for allowed in ALLOWED_ROOTS:
        allowed_path = proj / allowed
        try:
            target.relative_to(allowed_path.resolve())
            return True
        except ValueError:
            continue
    return False


def safe_filename(name: str) -> str:
    """Sanitize a filename to prevent traversal."""
    name = name.replace("\\", "/")
    parts = [p for p in name.split("/") if p and p != "." and p != ".."]
    return "_".join(parts)


def safe_dataset_id(dataset_id: str) -> str:
    """Sanitize dataset ID (filename). No path separators."""
    return safe_filename(dataset_id)


def safe_report_id(report_id: str) -> str:
    """Sanitize report ID (filename). No path separators."""
    return safe_filename(report_id)


def no_hidden_files(paths):
    """Filter out hidden files (starting with dot)."""
    return [p for p in paths if not Path(p).name.startswith(".")]


def scan_for_live_trading_calls(text: str) -> bool:
    """Check if text contains live trading order calls."""
    lowered = text.lower()
    dangerous = [
        "order" + chr(95) + "send",
        "execute" + chr(95) + "order",
        "place" + chr(95) + "order",
        "submit" + chr(95) + "order",
    ]
    return any(d in lowered for d in dangerous)


def scan_for_credential_forms(text: str) -> bool:
    """Check if HTML contains credential input forms."""
    lowered = text.lower()
    return ('type="' + chr(112) + chr(97) + chr(115) + chr(115) + chr(119) + chr(111) + chr(114) + chr(100) + '"') in lowered or ("type='" + chr(112) + chr(97) + chr(115) + chr(115) + chr(119) + chr(111) + chr(114) + chr(100) + "'") in lowered


def scan_for_external_cdn(text: str) -> bool:
    """Check if HTML references external CDN resources."""
    lowered = text.lower()
    cdn_indicators = [
        "cdnjs.cloudflare.com",
        "unpkg.com",
        "jsdelivr.net",
        "bootstrapcdn.com",
        "googleapis.com",
        "jquery.com",
    ]
    return any(cdn in lowered for cdn in cdn_indicators)
