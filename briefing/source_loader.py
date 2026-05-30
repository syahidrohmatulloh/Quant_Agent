"""Source loader for briefing inputs.

Loads JSON and JSONL safely from configured local paths only.
No arbitrary file reads. No .env reads. No credential files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json_source(path: Path, allow_missing: bool = False) -> Optional[Dict[str, Any]]:
    if not path.exists():
        if allow_missing:
            return None
        raise FileNotFoundError(f"Source not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    if not raw.strip():
        if allow_missing:
            return None
        raise ValueError(f"Source file empty: {path}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        if allow_missing:
            return None
        raise ValueError(f"Invalid JSON in {path}: {e}")
    return data


def load_jsonl_source(path: Path, allow_missing: bool = False) -> Optional[List[Dict[str, Any]]]:
    if not path.exists():
        if allow_missing:
            return None
        raise FileNotFoundError(f"Source not found: {path}")
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not records and not allow_missing:
        raise ValueError(f"No valid JSONL records in {path}")
    return records if records else (None if allow_missing else [])


def load_sources(config: Dict[str, Any], project_root: Path, allow_missing: bool = False) -> Dict[str, Any]:
    sources_config = config.get("sources", {})
    loaded = {}
    warnings = []

    for name, rel_path in sources_config.items():
        full_path = project_root / rel_path
        # Ensure resolved path is still under project_root
        try:
            resolved = full_path.resolve()
            root_resolved = project_root.resolve()
            if not str(resolved).startswith(str(root_resolved)):
                warnings.append(f"Source path escapes project root: {name}")
                loaded[name] = None
                continue
        except Exception:
            warnings.append(f"Cannot resolve source path: {name}")
            loaded[name] = None
            continue

        if not resolved.exists():
            msg = f"Missing source: {name} at {rel_path}"
            if allow_missing:
                warnings.append(msg)
                loaded[name] = None
            else:
                raise FileNotFoundError(msg)
            continue

        # Load based on extension
        suffix = resolved.suffix.lower()
        try:
            if suffix == ".jsonl" or suffix == ".jsonl" or str(resolved).endswith(".jsonl"):
                data = load_jsonl_source(resolved, allow_missing=allow_missing)
            else:
                data = load_json_source(resolved, allow_missing=allow_missing)
            loaded[name] = data
        except Exception as e:
            msg = f"Failed to load source {name}: {e}"
            if allow_missing:
                warnings.append(msg)
                loaded[name] = None
            else:
                raise

    return {"sources": loaded, "warnings": warnings}


def normalize_sources(loaded: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize loaded source data into a common structure."""
    sources = loaded.get("sources", {})
    normalized = {
        "latest_experiment_summary": sources.get("experiment_dashboard"),
        "latest_paper_orchestration_summary": sources.get("paper_orchestration_dashboard"),
        "latest_paper_simulator_portfolio": sources.get("paper_simulator_dashboard"),
        "paper_simulator_state": sources.get("paper_simulator_state"),
        "paper_simulator_pnl_records": sources.get("paper_simulator_pnl"),
        "latest_research_analytics_summary": sources.get("research_analytics_dashboard"),
        "data_manager_catalog": sources.get("data_manager_catalog"),
        "data_manager_import_log": sources.get("data_manager_import_log"),
    }
    return normalized
