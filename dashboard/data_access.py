"""
Data access layer for the Phase 14 dashboard.
Reads only from allowed directories. No broker calls. No credentials.
Reuses Phase 12 and Phase 13 modules.
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from dashboard.safety import (
    is_under_allowed_root,
    safe_dataset_id,
    safe_report_id,
    no_hidden_files,
    ALLOWED_ROOTS,
)
from dashboard.view_models import (
    DatasetViewModel,
    ExperimentConfigViewModel,
    ExperimentHistoryViewModel,
    ReportViewModel,
    HomeStatusViewModel,
)


def get_project_root() -> Path:
    """Infer project root from this file location."""
    return Path(__file__).resolve().parents[1]


def _resolve_under(root: Path, rel: str) -> Path:
    p = (root / rel).resolve()
    if not is_under_allowed_root(str(p), str(root)):
        raise PermissionError(f"Path not allowed: {p}")
    return p


def list_datasets(project_root: Optional[str] = None) -> List[DatasetViewModel]:
    root = Path(project_root) if project_root else get_project_root()
    data_dir = root / "data" / "market"
    if not data_dir.exists():
        return []

    results: List[DatasetViewModel] = []
    # Reuse Phase 12 dataset_catalog
    try:
        from market_data.dataset_catalog import scan_datasets
        datasets = scan_datasets(str(data_dir))
    except Exception:
        datasets = []
        for f in sorted(data_dir.iterdir()):
            if f.suffix.lower() not in (".csv", ".jsonl"):
                continue
            datasets.append({
                "filename": f.name,
                "path": str(f),
                "symbol": "",
                "timeframe": "",
                "source": "",
                "row_count": 0,
            })

    for d in datasets:
        dataset_id = safe_dataset_id(d["filename"])
        # Validate using Phase 12 csv_validator if available
        valid = True
        warnings: List[str] = []
        errors: List[str] = []
        try:
            from market_data.csv_validator import validate_csv
            vres = validate_csv(d["path"])
            valid = vres.get("valid", True)
            warnings = vres.get("warnings", [])
            errors = vres.get("errors", [])
        except Exception:
            pass

        results.append(DatasetViewModel(
            dataset_id=dataset_id,
            filename=d["filename"],
            path=d["path"],
            symbol=d.get("symbol", ""),
            timeframe=d.get("timeframe", ""),
            source=d.get("source", ""),
            row_count=d.get("row_count", 0),
            valid=valid,
            warnings=warnings,
            errors=errors,
        ))
    return results


def get_dataset_detail(dataset_id: str, project_root: Optional[str] = None) -> Optional[DatasetViewModel]:
    root = Path(project_root) if project_root else get_project_root()
    data_dir = root / "data" / "market"
    safe_id = safe_dataset_id(dataset_id)
    target = data_dir / safe_id
    if not target.exists() or not is_under_allowed_root(str(target), str(root)):
        return None

    # Reuse csv_validator
    valid = True
    warnings: List[str] = []
    errors: List[str] = []
    row_count = 0
    first_ts = None
    last_ts = None
    sample_last_5: List[Dict[str, Any]] = []
    symbol = ""
    timeframe = ""
    source = ""

    try:
        from market_data.csv_validator import validate_csv
        vres = validate_csv(str(target))
        valid = vres.get("valid", True)
        warnings = vres.get("warnings", [])
        errors = vres.get("errors", [])
        row_count = vres.get("row_count", 0)
        first_ts = vres.get("first_timestamp")
        last_ts = vres.get("last_timestamp")
        symbol = vres.get("inferred_symbol", "")
        timeframe = vres.get("inferred_timeframe", "")
        source = vres.get("inferred_source", "")
    except Exception as e:
        errors.append(f"Validation error: {e}")

    # Sample last 5 bars
    try:
        from market_data.csv_loader import load_csv
        bars = load_csv(str(target))
        sample_last_5 = [dict(b) for b in bars[-5:]] if len(bars) >= 5 else [dict(b) for b in bars]
    except Exception:
        pass

    vm = DatasetViewModel(
        dataset_id=safe_id,
        filename=safe_id,
        path=str(target),
        symbol=symbol,
        timeframe=timeframe,
        source=source,
        row_count=row_count,
        valid=valid,
        warnings=warnings,
        errors=errors,
    )
    # Attach extra fields dynamically for detail view
    vm.first_timestamp = first_ts
    vm.last_timestamp = last_ts
    vm.sample_last_5 = sample_last_5
    return vm


def list_experiment_configs(project_root: Optional[str] = None) -> List[ExperimentConfigViewModel]:
    root = Path(project_root) if project_root else get_project_root()
    configs: List[ExperimentConfigViewModel] = []
    for rel_dir in ("examples", "configs"):
        cfg_dir = root / rel_dir
        if not cfg_dir.exists():
            continue
        for f in sorted(cfg_dir.iterdir()):
            if f.suffix.lower() != ".json":
                continue
            if f.name.startswith("."):
                continue
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception as e:
                configs.append(ExperimentConfigViewModel(
                    path=str(f), name=f.name, valid=False,
                    paper_only=False, data_only=False,
                    errors=[f"JSON parse error: {e}"]
                ))
                continue

            name = data.get("name", f.name)
            paper_only = data.get("paper_only", False)
            data_only = data.get("data_only", False)
            errors: List[str] = []
            warnings: List[str] = []
            if not paper_only:
                errors.append("paper_only must be true")
            if not data_only:
                errors.append("data_only must be true")
            valid = len(errors) == 0
            configs.append(ExperimentConfigViewModel(
                path=str(f), name=name, valid=valid,
                paper_only=paper_only, data_only=data_only,
                errors=errors, warnings=warnings,
            ))
    return configs


def get_experiment_config_preview(config_path: str, project_root: Optional[str] = None) -> Dict[str, Any]:
    root = Path(project_root) if project_root else get_project_root()
    target = Path(config_path).resolve()
    if not is_under_allowed_root(str(target), str(root)):
        raise PermissionError(f"Config path not allowed: {target}")
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    symbols = data.get("symbols", [])
    strategies = data.get("strategies", [])
    missing_csvs = []
    for s in symbols:
        csv_p = s.get("csv", "")
        if csv_p and not Path(csv_p).exists():
            missing_csvs.append(csv_p)
    return {
        "name": data.get("name", ""),
        "symbols": [s.get("symbol", "") for s in symbols],
        "timeframes": [s.get("timeframe", "") for s in symbols],
        "strategies": [s.get("name", "") for s in strategies],
        "missing_csv_warnings": missing_csvs,
        "paper_only": data.get("paper_only", False),
        "data_only": data.get("data_only", False),
    }


def list_experiment_history(project_root: Optional[str] = None) -> List[ExperimentHistoryViewModel]:
    root = Path(project_root) if project_root else get_project_root()
    hist_dir = root / "reports" / "experiments" / "history"
    if not hist_dir.exists():
        return []
    hist_file = hist_dir / "experiment_history.jsonl"
    if not hist_file.exists():
        return []
    records: List[ExperimentHistoryViewModel] = []
    try:
        with open(hist_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                records.append(ExperimentHistoryViewModel(
                    run_id=rec.get("run_id", ""),
                    generated_at=rec.get("generated_at", ""),
                    experiment_name=rec.get("experiment_name", ""),
                    symbol_count=rec.get("symbol_count", 0),
                    strategy_count=rec.get("strategy_count", 0),
                    result_path=rec.get("result_path"),
                    dashboard_json_path=rec.get("dashboard_json_path"),
                ))
    except Exception:
        pass
    return records


def get_latest_dashboard_json(project_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    root = Path(project_root) if project_root else get_project_root()
    dash_dir = root / "reports" / "dashboard" / "experiments"
    if not dash_dir.exists():
        return None
    files = sorted([f for f in dash_dir.iterdir() if f.suffix.lower() == ".json" and not f.name.startswith(".")])
    if not files:
        return None
    latest = files[-1]
    try:
        with open(latest, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_reports(project_root: Optional[str] = None) -> List[ReportViewModel]:
    root = Path(project_root) if project_root else get_project_root()
    reports_dir = root / "reports" / "experiments"
    if not reports_dir.exists():
        return []
    results: List[ReportViewModel] = []
    for f in sorted(reports_dir.iterdir()):
        if f.suffix.lower() != ".md":
            continue
        if f.name.startswith("."):
            continue
        title = f.stem.replace("_", " ").title()
        generated_at = None
        try:
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("Generated:"):
                        generated_at = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass
        results.append(ReportViewModel(
            report_id=f.name,
            title=title,
            generated_at=generated_at,
            path=str(f),
        ))
    return results


def get_report_detail(report_id: str, project_root: Optional[str] = None) -> Optional[str]:
    root = Path(project_root) if project_root else get_project_root()
    safe_id = safe_report_id(report_id)
    target = (root / "reports" / "experiments" / safe_id).resolve()
    if not target.exists() or not is_under_allowed_root(str(target), str(root)):
        return None
    try:
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def get_home_status(project_root: Optional[str] = None) -> HomeStatusViewModel:
    root = Path(project_root) if project_root else get_project_root()
    datasets = list_datasets(str(root))
    reports = list_reports(str(root))
    dash_dir = root / "reports" / "dashboard" / "experiments"
    dash_count = 0
    if dash_dir.exists():
        dash_count = len([f for f in dash_dir.iterdir() if f.suffix.lower() == ".json" and not f.name.startswith(".")])

    history = list_experiment_history(str(root))
    latest_name = None
    latest_time = None
    if history:
        latest = history[-1]
        latest_name = latest.experiment_name
        latest_time = latest.generated_at

    return HomeStatusViewModel(
        dataset_count=len(datasets),
        experiment_report_count=len(reports),
        dashboard_export_count=dash_count,
        latest_experiment_name=latest_name,
        latest_experiment_time=latest_time,
    )
