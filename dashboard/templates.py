"""
HTML template rendering for the Phase 14 dashboard.
Uses inline CSS only. No external CDN. Escapes all dynamic content.
Phase 25: adds action center page and fixes operator status rendering.
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
    latest = f'<p>Latest experiment: <strong>{_esc(status.latest_experiment_name)}</strong> at {_esc(status.latest_experiment_time)}</p>' if status.latest_experiment_name else '<p>No experiments yet.</p>'
    body = f"""
<h2>Quant_Agent Local Dashboard</h2>
<p>This is a local research dashboard for inspecting market data, experiment configs, and paper-only decision reports.</p>
<div style="display:flex;gap:20px;margin:20px 0;">
  <div style="background:#f0f0f0;padding:15px;border-radius:8px;min-width:120px;text-align:center;">
    <div style="font-size:28px;font-weight:bold;">{_esc(status.dataset_count)}</div>
    <div>CSV Datasets</div>
  </div>
  <div style="background:#f0f0f0;padding:15px;border-radius:8px;min-width:120px;text-align:center;">
    <div style="font-size:28px;font-weight:bold;">{_esc(status.experiment_report_count)}</div>
    <div>Experiment Reports</div>
  </div>
  <div style="background:#f0f0f0;padding:15px;border-radius:8px;min-width:120px;text-align:center;">
    <div style="font-size:28px;font-weight:bold;">{_esc(status.dashboard_export_count)}</div>
    <div>Dashboard JSON Exports</div>
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
            status_badge = 'Valid' if d.valid else 'Invalid'
            warn_count = len(d.warnings)
            err_count = len(d.errors)
            issues = ""
            if warn_count:
                issues += f' {warn_count} warnings'
            if err_count:
                issues += f' {err_count} errors'
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
<h2>Datasets</h2>
<table>
<thead>
<tr><th>Filename</th><th>Symbol</th><th>Timeframe</th><th>Source</th><th>Rows</th><th>Status</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
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
        warn_list += f"<li>{_esc(w)}</li>\n"
    err_list = ""
    for e in vm.errors:
        err_list += f"<li>{_esc(e)}</li>\n"
    body = f"""
<h2>Dataset: {_esc(vm.filename)}</h2>
<p><strong>Path:</strong> <code>{_esc(vm.path)}</code></p>
<p><strong>Symbol:</strong> {_esc(vm.symbol)}</p>
<p><strong>Timeframe:</strong> {_esc(vm.timeframe)}</p>
<p><strong>Source:</strong> {_esc(vm.source)}</p>
<p><strong>Row count:</strong> {_esc(vm.row_count)}</p>
<p><strong>First timestamp:</strong> {_esc(first_ts)}</p>
<p><strong>Last timestamp:</strong> {_esc(last_ts)}</p>
<p><strong>Validation:</strong> {"Valid" if vm.valid else "Invalid"}</p>
<h3>Warnings</h3>
<ul>
{warn_list or "<li>- None</li>\n"}
</ul>
<h3>Errors</h3>
<ul>
{err_list or "<li>- None</li>\n"}
</ul>
{sample_html}
"""
    return wrap_html(f"Dataset {_esc(vm.filename)}", body)

def render_experiment_configs(configs: List[ExperimentConfigViewModel]) -> str:
    if not configs:
        rows = '<tr><td colspan="4">No experiment configs found</td></tr>'
    else:
        rows = ""
        for c in configs:
            status = 'OK' if c.valid else 'Invalid'
            paper = 'paper_only' if c.paper_only else 'missing'
            data = 'data_only' if c.data_only else 'missing'
            rows += f"""
<tr>
  <td>{_esc(c.name)}</td>
  <td>{status}</td>
  <td>{paper} {data}</td>
  <td><a href="/experiments/run?config={_esc(c.path)}">Preview</a></td>
</tr>
"""
    body = f"""
<h2>Experiment Configs</h2>
<table>
<thead>
<tr><th>Name</th><th>Valid</th><th>Safety</th><th>Preview</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
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
            missing_html += f"<li>{_esc(m)}</li>\n"
        missing_html += "</ul>"
    body = f"""
<h2>Experiment Run Preview</h2>
<p><strong>Config:</strong> <code>{_esc(config_path)}</code></p>
<p><strong>Name:</strong> {_esc(preview.get("name", ""))}</p>
<p><strong>Symbols:</strong> {_esc(symbols)}</p>
<p><strong>Timeframes:</strong> {_esc(", ".join(preview.get("timeframes", [])))}</p>
<p><strong>Strategies:</strong> {_esc(strategies)}</p>
<p><strong>Paper-only:</strong> {_esc(preview.get("paper_only", False))}</p>
<p><strong>Data-only:</strong> {_esc(preview.get("data_only", False))}</p>
{missing_html}
<h3>Run from Terminal</h3>
<pre>python3 tools/run_strategy_experiment.py --config {_esc(config_path)}</pre>
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
    {f'<a href="/reports/{_esc(h.result_path)}">Result</a>' if h.result_path else ""}
    {f'<a href="/dashboard/latest">JSON</a>' if h.dashboard_json_path else ""}
  </td>
</tr>
"""
    body = f"""
<h2>Experiment History</h2>
<table>
<thead>
<tr><th>Run ID</th><th>Name</th><th>Generated</th><th>Symbols / Strategies</th><th>Links</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
"""
    return wrap_html("Experiment History", body)

def render_latest_dashboard(data: Optional[Dict[str, Any]]) -> str:
    if data is None:
        body = '<h2>Latest Dashboard JSON</h2><p>No dashboard JSON exports found yet.</p>'
        return wrap_html("Latest Dashboard", body)
    symbols = data.get("symbols", [])
    summary = data.get("summary", {})
    body = f"""
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
<thead>
<tr><th>Symbol</th><th>Timeframe</th><th>Signal</th><th>Strategies</th></tr>
</thead>
<tbody>
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
    body += "</tbody></table>"
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
  <td><code>{_esc(r.path)}</code></td>
</tr>
"""
    body = f"""
<h2>Reports</h2>
<table>
<thead>
<tr><th>Title</th><th>Generated</th><th>Path</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
"""
    return wrap_html("Reports", body)

def render_report_detail(report_id: str, content: str) -> str:
    escaped = _esc(content)
    body = f"""
<h2>Report: {_esc(report_id)}</h2>
<pre>{escaped}</pre>
"""
    return wrap_html(f"Report {_esc(report_id)}", body)

def render_operator_status(project_root, config=None):
    """Render local operator status page.

    PAPER-ONLY / DATA-ONLY. No live trading.
    """
    from local_app.operator_status import build_operator_status, render_operator_summary

    status = build_operator_status(config or {}, project_root, allow_missing=True)
    summary = render_operator_summary(status)
    escaped_summary = html.escape(summary)

    return f"""
<div style="padding:20px;">
<h2>Quant_Agent Operator Status</h2>
<p><strong>PAPER-ONLY / DATA-ONLY.</strong> No live trading. No order submission.</p>
<pre style="background:#f5f5f5;padding:15px;border-radius:6px;overflow:auto;">{escaped_summary}</pre>
<p><a href="/action-center">View Action Center</a></p>
</div>
"""

def render_action_center(ac) -> str:
    """Render action center as an HTML page.

    PAPER-ONLY / DATA-ONLY. No live trading.
    """
    # Build warning categories HTML
    cat_html = ""
    if ac.warning_categories:
        cat_html += '<table style="width:100%;border-collapse:collapse;margin:10px 0;">'
        cat_html += '<thead><tr><th style="text-align:left;padding:8px;border-bottom:2px solid #ccc;">Category</th><th style="text-align:left;padding:8px;border-bottom:2px solid #ccc;">Count</th><th style="text-align:left;padding:8px;border-bottom:2px solid #ccc;">Items</th></tr></thead><tbody>'
        for cat, items in ac.warning_categories.items():
            if items:
                items_list = "<br>".join(html.escape(item) for item in items)
                cat_html += f'<tr><td style="padding:8px;border-bottom:1px solid #eee;"><strong>{_esc(cat.upper())}</strong></td><td style="padding:8px;border-bottom:1px solid #eee;">{len(items)}</td><td style="padding:8px;border-bottom:1px solid #eee;font-size:13px;">{items_list}</td></tr>'
        cat_html += '</tbody></table>'
    else:
        cat_html = '<p>No categorized warnings.</p>'

    # Blockers
    blockers_html = ""
    if ac.blockers:
        blockers_html += '<ul style="color:#c00;">'
        for b in ac.blockers:
            blockers_html += f'<li><strong>{_esc(b)}</strong></li>'
        blockers_html += '</ul>'
    else:
        blockers_html = '<p style="color:#080;">None</p>'

    # Warnings
    warnings_html = ""
    if ac.warnings:
        warnings_html += '<ul style="color:#a60;">'
        for w in ac.warnings:
            warnings_html += f'<li>{_esc(w)}</li>'
        warnings_html += '</ul>'
    else:
        warnings_html = '<p style="color:#080;">None</p>'

    # Action items helpers
    def _items_html(items, color="#06c"):
        if not items:
            return '<p style="color:#888;">None</p>'
        out = f'<ul style="color:{color};">'
        for item in items:
            out += f'<li>{_esc(item)}</li>'
        out += '</ul>'
        return out

    # Generated outputs
    outputs_html = ""
    if ac.generated_outputs:
        outputs_html += '<ul>'
        for p in ac.generated_outputs:
            outputs_html += f'<li><code>{_esc(p)}</code></li>'
        outputs_html += '</ul>'
    else:
        outputs_html = '<p style="color:#888;">None yet</p>'

    # Next safe commands
    commands_html = ""
    if ac.next_safe_commands:
        commands_html += '<ul>'
        for cmd in ac.next_safe_commands:
            commands_html += f'<li><code>{_esc(cmd)}</code></li>'
        commands_html += '</ul>'
    else:
        commands_html = '<p style="color:#888;">None</p>'

    # Overall badge color
    overall_color = "#080" if ac.overall == "OK" else ("#a60" if ac.overall == "OK_WITH_WARNINGS" else "#c00")

    body = f"""
<div style="padding:20px;">
<h2>Action Center</h2>
<p><strong style="color:#c00;">PAPER-ONLY / DATA-ONLY.</strong> No live trading. No order submission.</p>

<div style="background:#f8f8f8;padding:15px;border-radius:8px;margin:15px 0;">
  <div style="font-size:24px;font-weight:bold;color:{overall_color};">Overall: {_esc(ac.overall)}</div>
  <div style="margin-top:8px;">Mode: {_esc(ac.mode)} | Paper-only: {_esc(ac.paper_only)} | Data-only: {_esc(ac.data_only)} | No order submission: {_esc(ac.no_order_submission)}</div>
  <div style="margin-top:8px;color:#666;font-size:13px;">{_esc(ac.disclaimer)}</div>
</div>

<h3>Readiness</h3>
<div style="background:#f0f0f0;padding:12px;border-radius:6px;">
  <p><strong>Score:</strong> {_esc(ac.readiness_score if ac.readiness_score is not None else "N/A")}/100</p>
  <p><strong>Grade:</strong> {_esc(ac.readiness_grade or "N/A")}</p>
  <p><strong>Status:</strong> {_esc(ac.readiness_status or "N/A")}</p>
  <p><strong>Latest operator run:</strong> {_esc(ac.latest_operator_run or "N/A")}</p>
</div>

<h3>Warning Categories</h3>
{cat_html}

<div style="display:flex;gap:20px;margin:20px 0;">
  <div style="flex:1;background:#fff0f0;padding:15px;border-radius:8px;">
    <h4 style="margin-top:0;color:#c00;">Blockers ({len(ac.blockers)})</h4>
    {blockers_html}
  </div>
  <div style="flex:1;background:#fff8f0;padding:15px;border-radius:8px;">
    <h4 style="margin-top:0;color:#a60;">Warnings ({len(ac.warnings)})</h4>
    {warnings_html}
  </div>
</div>

<h3>Action Items</h3>
<div style="display:flex;gap:20px;flex-wrap:wrap;margin:15px 0;">
  <div style="flex:1;min-width:220px;background:#f0f8ff;padding:12px;border-radius:6px;">
    <h4 style="margin-top:0;color:#06c;">Readiness</h4>
    {_items_html(ac.readiness_action_items)}
  </div>
  <div style="flex:1;min-width:220px;background:#f0f8ff;padding:12px;border-radius:6px;">
    <h4 style="margin-top:0;color:#06c;">Workflow</h4>
    {_items_html(ac.workflow_action_items)}
  </div>
  <div style="flex:1;min-width:220px;background:#f0f8ff;padding:12px;border-radius:6px;">
    <h4 style="margin-top:0;color:#06c;">Briefing</h4>
    {_items_html(ac.briefing_action_items)}
  </div>
  <div style="flex:1;min-width:220px;background:#f0f8ff;padding:12px;border-radius:6px;">
    <h4 style="margin-top:0;color:#06c;">Dashboard</h4>
    {_items_html(ac.dashboard_action_items)}
  </div>
</div>

<h3>Latest Generated Outputs</h3>
{outputs_html}

<h3>Next Safe Commands</h3>
{commands_html}

<p style="margin-top:30px;color:#888;font-size:12px;">
  Reminder: reports/logs/local outputs should not be committed.
  This tool does not approve or enable live trading.
  No broker calls. No live network. No credential prompts.
  No actual email send. No actual Telegram send. No cron install.
</p>
</div>
"""
    return wrap_html("Action Center", body)
