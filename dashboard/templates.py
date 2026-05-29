"""
HTML template rendering for the Phase 14 dashboard.
Uses inline CSS only. No external CDN. Escapes all dynamic content.
"""
import html
from typing import List, Dict, Any, Optional

from dashboard.static_assets import wrap_html
from dashboard.view_models import (
    DatasetViewModel,
    ExperimentConfigViewModel,
    ExperimentHistoryViewModel,
    ReportViewModel,
    HomeStatusViewModel,
)


def _esc(text: Any) -> str:
    return html.escape(str(text)) if text is not None else ""


def render_home(status: HomeStatusViewModel) -> str:
    latest = f'<p class="small">Latest experiment: <strong>{_esc(status.latest_experiment_name)}</strong> at {_esc(status.latest_experiment_time)}</p>' if status.latest_experiment_name else '<p class="small">No experiments yet.</p>'
    body = f"""
<div class="card">
  <h2>Quant_Agent Local Dashboard</h2>
  <p>This is a local research dashboard for inspecting market data, experiment configs, and paper-only decision reports.</p>
</div>
<div class="grid">
  <div class="stat">
    <div class="number">{_esc(status.dataset_count)}</div>
    <div class="label">CSV Datasets</div>
  </div>
  <div class="stat">
    <div class="number">{_esc(status.experiment_report_count)}</div>
    <div class="label">Experiment Reports</div>
  </div>
  <div class="stat">
    <div class="number">{_esc(status.dashboard_export_count)}</div>
    <div class="label">Dashboard JSON Exports</div>
  </div>
</div>
{latest}
"""
    return wrap_html("Home", body)


def render_datasets(datasets: List[DatasetViewModel]) -> str:
    if not datasets:
        rows = '<tr><td colspan="6">No datasets found in data/market</td></tr>'
    else:
        rows = ""
        for d in datasets:
            status_badge = '<span class="badge badge-ok">Valid</span>' if d.valid else '<span class="badge badge-err">Invalid</span>'
            warn_count = len(d.warnings)
            err_count = len(d.errors)
            issues = ""
            if warn_count:
                issues += f' <span class="badge badge-warn">{warn_count} warnings</span>'
            if err_count:
                issues += f' <span class="badge badge-err">{err_count} errors</span>'
            rows += f"""
<tr>
  <td><a href="/datasets/{_esc(d.dataset_id)}">{_esc(d.filename)}</a></td>
  <td>{_esc(d.symbol)}</td>
  <td>{_esc(d.timeframe)}</td>
  <td>{_esc(d.source)}</td>
  <td>{_esc(d.row_count)}</td>
  <td>{status_badge}{issues}</td>
</tr>
"""
    body = f"""
<div class="card">
  <h2>Datasets</h2>
  <table>
    <tr>
      <th>Filename</th>
      <th>Symbol</th>
      <th>Timeframe</th>
      <th>Source</th>
      <th>Rows</th>
      <th>Status</th>
    </tr>
    {rows}
  </table>
</div>
"""
    return wrap_html("Datasets", body)


def render_dataset_detail(vm: DatasetViewModel) -> str:
    first_ts = getattr(vm, "first_timestamp", None) or "N/A"
    last_ts = getattr(vm, "last_timestamp", None) or "N/A"
    sample = getattr(vm, "sample_last_5", [])
    sample_html = ""
    if sample:
        sample_html += "<h3>Sample Last 5 Bars</h3><pre>"
        for row in sample:
            sample_html += html.escape(str(row)) + "\n"
        sample_html += "</pre>"
    warn_list = ""
    for w in vm.warnings:
        warn_list += f"<li>{_esc(w)}</li>"
    err_list = ""
    for e in vm.errors:
        err_list += f"<li>{_esc(e)}</li>"
    body = f"""
<div class="card">
  <h2>Dataset: {_esc(vm.filename)}</h2>
  <p><strong>Path:</strong> <span class="code">{_esc(vm.path)}</span></p>
  <p><strong>Symbol:</strong> {_esc(vm.symbol)}</p>
  <p><strong>Timeframe:</strong> {_esc(vm.timeframe)}</p>
  <p><strong>Source:</strong> {_esc(vm.source)}</p>
  <p><strong>Row count:</strong> {_esc(vm.row_count)}</p>
  <p><strong>First timestamp:</strong> {_esc(first_ts)}</p>
  <p><strong>Last timestamp:</strong> {_esc(last_ts)}</p>
  <p><strong>Validation:</strong> {"Valid" if vm.valid else "Invalid"}</p>
  <h3>Warnings</h3>
  <ul>{warn_list or "<li>None</li>"}</ul>
  <h3>Errors</h3>
  <ul>{err_list or "<li>None</li>"}</ul>
  {sample_html}
</div>
"""
    return wrap_html(f"Dataset {_esc(vm.filename)}", body)


def render_experiment_configs(configs: List[ExperimentConfigViewModel]) -> str:
    if not configs:
        rows = '<tr><td colspan="4">No experiment configs found</td></tr>'
    else:
        rows = ""
        for c in configs:
            status = '<span class="badge badge-ok">OK</span>' if c.valid else '<span class="badge badge-err">Invalid</span>'
            paper = '<span class="badge badge-ok">paper_only</span>' if c.paper_only else '<span class="badge badge-err">missing</span>'
            data = '<span class="badge badge-ok">data_only</span>' if c.data_only else '<span class="badge badge-err">missing</span>'
            rows += f"""
<tr>
  <td>{_esc(c.name)}</td>
  <td>{status}</td>
  <td>{paper} {data}</td>
  <td><a href="/experiments/run?config={_esc(c.path)}">Preview</a></td>
</tr>
"""
    body = f"""
<div class="card">
  <h2>Experiment Configs</h2>
  <table>
    <tr><th>Name</th><th>Valid</th><th>Safety</th><th>Preview</th></tr>
    {rows}
  </table>
</div>
"""
    return wrap_html("Experiment Configs", body)


def render_experiment_run_preview(preview: Dict[str, Any], config_path: str) -> str:
    symbols = ", ".join(preview.get("symbols", []))
    strategies = ", ".join(preview.get("strategies", []))
    missing = preview.get("missing_csv_warnings", [])
    missing_html = ""
    if missing:
        missing_html = "<h3>Missing CSV Warnings</h3><ul>"
        for m in missing:
            missing_html += f"<li>{_esc(m)}</li>"
        missing_html += "</ul>"
    body = f"""
<div class="card">
  <h2>Experiment Run Preview</h2>
  <p><strong>Config:</strong> <span class="code">{_esc(config_path)}</span></p>
  <p><strong>Name:</strong> {_esc(preview.get("name", ""))}</p>
  <p><strong>Symbols:</strong> {_esc(symbols)}</p>
  <p><strong>Timeframes:</strong> {_esc(", ".join(preview.get("timeframes", [])))}</p>
  <p><strong>Strategies:</strong> {_esc(strategies)}</p>
  <p><strong>Paper-only:</strong> {_esc(preview.get("paper_only", False))}</p>
  <p><strong>Data-only:</strong> {_esc(preview.get("data_only", False))}</p>
  {missing_html}
  <h3>Run from Terminal</h3>
  <pre>python3 tools/run_strategy_experiment.py --config {_esc(config_path)}</pre>
</div>
"""
    return wrap_html("Experiment Preview", body)


def render_experiment_history(history: List[ExperimentHistoryViewModel]) -> str:
    if not history:
        rows = '<tr><td colspan="5">No experiment history yet</td></tr>'
    else:
        rows = ""
        for h in history:
            rows += f"""
<tr>
  <td>{_esc(h.run_id)}</td>
  <td>{_esc(h.experiment_name)}</td>
  <td>{_esc(h.generated_at)}</td>
  <td>{_esc(h.symbol_count)} / {_esc(h.strategy_count)}</td>
  <td>
    {f'<a href="file://{_esc(h.result_path)}">Result</a>' if h.result_path else ""}
    {f'<a href="file://{_esc(h.dashboard_json_path)}">JSON</a>' if h.dashboard_json_path else ""}
  </td>
</tr>
"""
    body = f"""
<div class="card">
  <h2>Experiment History</h2>
  <table>
    <tr><th>Run ID</th><th>Name</th><th>Generated</th><th>Symbols / Strategies</th><th>Links</th></tr>
    {rows}
  </table>
</div>
"""
    return wrap_html("Experiment History", body)


def render_latest_dashboard(data: Optional[Dict[str, Any]]) -> str:
    if data is None:
        body = '<div class="card"><h2>Latest Dashboard JSON</h2><p>No dashboard JSON exports found yet.</p></div>'
        return wrap_html("Latest Dashboard", body)
    symbols = data.get("symbols", [])
    summary = data.get("summary", {})
    body = f"""
<div class="card">
  <h2>Latest Dashboard JSON</h2>
  <p><strong>Experiment:</strong> {_esc(data.get("experiment_name", ""))}</p>
  <p><strong>Generated:</strong> {_esc(data.get("generated_at", ""))}</p>
  <p><strong>Paper-only:</strong> {_esc(data.get("paper_only", False))}</p>
  <p><strong>Data-only:</strong> {_esc(data.get("data_only", False))}</p>
  <h3>Summary</h3>
  <p>Symbols: {_esc(summary.get("symbol_count", 0))} | 
     LONG: {_esc(summary.get("consensus_long", 0))} | 
     SHORT: {_esc(summary.get("consensus_short", 0))} | 
     NEUTRAL: {_esc(summary.get("consensus_neutral", 0))}</p>
  <h3>Per-Symbol Consensus</h3>
  <table>
    <tr><th>Symbol</th><th>Timeframe</th><th>Signal</th><th>Strategies</th></tr>
"""
    for s in symbols:
        consensus = s.get("consensus", {})
        signal = consensus.get("consensus_signal", "N/A")
        strat_count = len(s.get("strategies", []))
        body += f"""
    <tr>
      <td>{_esc(s.get("symbol", ""))}</td>
      <td>{_esc(s.get("timeframe", ""))}</td>
      <td>{_esc(signal)}</td>
      <td>{_esc(strat_count)}</td>
    </tr>
"""
    body += "  </table></div>"
    return wrap_html("Latest Dashboard", body)


def render_reports(reports: List[ReportViewModel]) -> str:
    if not reports:
        rows = '<tr><td colspan="3">No reports found</td></tr>'
    else:
        rows = ""
        for r in reports:
            rows += f"""
<tr>
  <td><a href="/reports/{_esc(r.report_id)}">{_esc(r.title)}</a></td>
  <td>{_esc(r.generated_at or "N/A")}</td>
  <td><span class="code">{_esc(r.path)}</span></td>
</tr>
"""
    body = f"""
<div class="card">
  <h2>Reports</h2>
  <table>
    <tr><th>Title</th><th>Generated</th><th>Path</th></tr>
    {rows}
  </table>
</div>
"""
    return wrap_html("Reports", body)


def render_report_detail(report_id: str, content: str) -> str:
    escaped = _esc(content)
    body = f"""
<div class="card">
  <h2>Report: {_esc(report_id)}</h2>
  <pre>{escaped}</pre>
</div>
"""
    return wrap_html(f"Report {_esc(report_id)}", body)
