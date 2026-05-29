#!/usr/bin/env python3
"""
Generate a static HTML summary from existing dashboard JSON and datasets.
No server required. Paper-only disclaimer included.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.static_assets import INLINE_CSS, wrap_html
from dashboard.data_access import (
    list_datasets,
    list_experiment_configs,
    list_experiment_history,
    get_latest_dashboard_json,
    list_reports,
    get_home_status,
)


def generate_static_html(project_root: Path) -> str:
    status = get_home_status(str(project_root))
    datasets = list_datasets(str(project_root))
    configs = list_experiment_configs(str(project_root))
    history = list_experiment_history(str(project_root))
    latest_dash = get_latest_dashboard_json(str(project_root))
    reports = list_reports(str(project_root))

    # Build body content
    latest = f'<p class="small">Latest experiment: <strong>{latest_dash.get("experiment_name", "N/A") if latest_dash else "N/A"}</strong></p>' if latest_dash else '<p class="small">No experiments yet.</p>'

    dataset_rows = ""
    for d in datasets:
        badge = '<span class="badge badge-ok">Valid</span>' if d.valid else '<span class="badge badge-err">Invalid</span>'
        dataset_rows += f"<tr><td>{d.filename}</td><td>{d.symbol}</td><td>{d.timeframe}</td><td>{d.row_count}</td><td>{badge}</td></tr>"

    config_rows = ""
    for c in configs:
        badge = '<span class="badge badge-ok">OK</span>' if c.valid else '<span class="badge badge-err">Invalid</span>'
        config_rows += f"<tr><td>{c.name}</td><td>{badge}</td><td>{c.paper_only}</td><td>{c.data_only}</td></tr>"

    history_rows = ""
    for h in history:
        history_rows += f"<tr><td>{h.run_id}</td><td>{h.experiment_name}</td><td>{h.generated_at}</td><td>{h.symbol_count}/{h.strategy_count}</td></tr>"

    report_rows = ""
    for r in reports:
        report_rows += f"<tr><td>{r.title}</td><td>{r.generated_at or 'N/A'}</td></tr>"

    dash_summary = ""
    if latest_dash:
        summary = latest_dash.get("summary", {})
        dash_summary = f"""
<p><strong>Experiment:</strong> {latest_dash.get('experiment_name', '')}</p>
<p>Symbols: {summary.get('symbol_count', 0)} | LONG: {summary.get('consensus_long', 0)} | SHORT: {summary.get('consensus_short', 0)} | NEUTRAL: {summary.get('consensus_neutral', 0)}</p>
"""

    body = f"""
<div class="card">
  <h2>Quant_Agent Static Summary</h2>
  <p>Generated at {datetime.now(timezone.utc).isoformat()}</p>
</div>
<div class="grid">
  <div class="stat"><div class="number">{status.dataset_count}</div><div class="label">Datasets</div></div>
  <div class="stat"><div class="number">{status.experiment_report_count}</div><div class="label">Reports</div></div>
  <div class="stat"><div class="number">{status.dashboard_export_count}</div><div class="label">JSON Exports</div></div>
</div>
{latest}
<div class="card">
  <h2>Datasets</h2>
  <table><tr><th>Filename</th><th>Symbol</th><th>TF</th><th>Rows</th><th>Status</th></tr>{dataset_rows or '<tr><td colspan="5">No datasets</td></tr>'}</table>
</div>
<div class="card">
  <h2>Experiment Configs</h2>
  <table><tr><th>Name</th><th>Valid</th><th>Paper</th><th>Data</th></tr>{config_rows or '<tr><td colspan="4">No configs</td></tr>'}</table>
</div>
<div class="card">
  <h2>Experiment History</h2>
  <table><tr><th>Run ID</th><th>Name</th><th>Generated</th><th>Syms/Strats</th></tr>{history_rows or '<tr><td colspan="4">No history</td></tr>'}</table>
</div>
<div class="card">
  <h2>Latest Dashboard JSON</h2>
  {dash_summary or '<p>No dashboard JSON available.</p>'}
</div>
<div class="card">
  <h2>Reports</h2>
  <table><tr><th>Title</th><th>Generated</th></tr>{report_rows or '<tr><td colspan="2">No reports</td></tr>'}</table>
</div>
"""
    return wrap_html("Static Summary", body)


def main():
    parser = argparse.ArgumentParser(description="Export static HTML dashboard summary")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="Project root directory")
    args = parser.parse_args()

    html_content = generate_static_html(Path(args.project_root))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Static HTML exported to: {out_path}")


if __name__ == "__main__":
    main()
