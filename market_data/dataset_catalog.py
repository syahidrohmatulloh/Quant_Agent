"""
Scan and catalog market datasets from a directory.
No network. No broker credentials.
"""
import csv
from typing import List, Dict, Any
from pathlib import Path

from market_data.csv_schema import infer_from_filename


def scan_datasets(data_dir: str = "data/market") -> List[Dict[str, Any]]:
    """Scan directory for CSV/JSONL datasets and infer metadata."""
    p = Path(data_dir)
    if not p.exists():
        return []
    datasets = []
    for f in sorted(p.iterdir()):
        if f.suffix.lower() not in (".csv", ".jsonl"):
            continue
        meta = infer_from_filename(f.name)
        row_count = 0
        if f.suffix.lower() == ".csv":
            try:
                with open(f, newline="", encoding="utf-8") as fh:
                    reader = csv.reader(fh)
                    next(reader, None)  # skip header
                    for _ in reader:
                        row_count += 1
            except Exception:
                pass
        datasets.append({
            "filename": f.name,
            "path": str(f),
            "symbol": meta.symbol,
            "timeframe": meta.timeframe,
            "source": meta.source,
            "row_count": row_count,
        })
    return datasets


def list_datasets_table(data_dir: str = "data/market") -> str:
    """Return a formatted table string of datasets."""
    datasets = scan_datasets(data_dir)
    if not datasets:
        return f"No datasets found in {data_dir}"
    lines = [f"{'Filename':<30} {'Symbol':<10} {'TF':<6} {'Source':<10} {'Rows':<8}",
             "-" * 70]
    for d in datasets:
        lines.append(f"{d['filename']:<30} {d['symbol']:<10} {d['timeframe']:<6} {d['source']:<10} {d['row_count']:<8}")
    return "\n".join(lines)
