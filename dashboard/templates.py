"""
HTML template rendering for the Phase 14 dashboard.
Uses inline CSS only. No external CDN. Escapes all dynamic content.
Phase 25: adds action center page and fixes operator status rendering.
Phase 26: adds research insights page.
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
    latest = f'<p>Latest experiment: <b>{_esc(status.latest_experiment_name)}</b> at {_esc(status.latest_experiment_time)}</p>' if status.latest_experiment_name else '<p>No experiments yet.</p>'
    body = f"""
<h2>Quant_Agent Local Dashboard</h2>
<p>This is a local research dashboard for inspecting market data, experiment configs, and paper-only decision reports.</p>
<ul>
  <li>{_esc(status.dataset_count)} CSV Datasets</li>
  <li>{_esc(status.experiment_report_count)} Experiment Reports</li>
  <li>{_esc(status.dashboard_export_count)} Dashboard JSON Exports</li>
</ul>
{latest}
<p><a href="/research-insights">Research Insights</a> | <a href="/operator">Operator Status</a> | <a href="/action-center">Action Center</a></p>
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
  <td>{_esc(d.filename)}</td>
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
  <tr><th>Filename</th><th>Symbol</th><th>Timeframe</th><th>Source</th><th>Rows</th><th>Status</th></tr>
  {rows}
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
<p><b>Path:</b> <code>{_esc(vm.path)}</code></p>
<p><b>Symbol:</b> {_esc(vm.symbol)}</p>
<p><b>Timeframe:</b> {_esc(vm.timeframe)}</p>
<p><b>Source:</b> {_esc(vm.source)}</p>
<p><b>Row count:</b> {_esc(vm.row_count)}</p>
<p><b>First timestamp:</b> {_esc(first_ts)}</p>
<p><b>Last timestamp:</b> {_esc(last_ts)}</p>
<p><b>Validation:</b> {"Valid" if vm.valid else "Invalid"}</p>
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
  <tr><th>Name</th><th>Valid</th><th>Safety</th><th>Preview</th></tr>
  {rows}
</table>
"""
    return wrap_html("Experiment Configs", body)

def render_experiment_run_preview(preview: Dict[str, Any], config_path: str) -> str:
    symbols = ", ".join(preview.get("symbols", []))
    strategies = ", ".join(preview.get("strategies", []))
    missing = preview.get("missing_csv_warnings", [])
    missing_html = ""
    if missing:
        missing_html = "<h3>Missing CSV Warnings</h3>\n"
        for m in missing:
            missing_html += f"<li>{_esc(m)}</li>\n"
        missing_html += "<p></p>"
    body = f"""
<h2>Experiment Run Preview</h2>
<p><b>Config:</b> <code>{_esc(config_path)}</code></p>
<p><b>Name:</b> {_esc(preview.get("name", ""))}</p>
<p><b>Symbols:</b> {_esc(symbols)}</p>
<p><b>Timeframes:</b> {_esc(", ".join(preview.get("timeframes", [])))}</p>
<p><b>Strategies:</b> {_esc(strategies)}</p>
<p><b>Paper-only:</b> {_esc(preview.get("paper_only", False))}</p>
<p><b>Data-only:</b> {_esc(preview.get("data_only", False))}</p>
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
  <tr><th>Run ID</th><th>Name</th><th>Generated</th><th>Symbols / Strategies</th><th>Links</th></tr>
  {rows}
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
<p><b>Experiment:</b> {_esc(data.get("experiment_name", ""))}</p>
<p><b>Generated:</b> {_esc(data.get("generated_at", ""))}</p>
<p><b>Paper-only:</b> {_esc(data.get("paper_only", False))}</p>
<p><b>Data-only:</b> {_esc(data.get("data_only", False))}</p>
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
    body += "</table>"
    return wrap_html("Latest Dashboard", body)

def render_reports(reports: List[ReportViewModel]) -> str:
    if not reports:
        rows = '<tr><td colspan="3">No reports found</td></tr>'
    else:
        rows = ""
        for r in reports:
            rows += f"""
<tr>
  <td>{_esc(r.title)}</td>
  <td>{_esc(r.generated_at or "N/A")}</td>
  <td><code>{_esc(r.path)}</code></td>
</tr>
"""
    body = f"""
<h2>Reports</h2>
<table>
  <tr><th>Title</th><th>Generated</th><th>Path</th></tr>
  {rows}
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
<h2>Quant_Agent Operator Status</h2>
<p><b>PAPER-ONLY / DATA-ONLY.</b> No live trading. No order submission.</p>
<pre>{escaped_summary}</pre>
<p><a href="/action-center">View Action Center</a></p>
<p><a href="/research-insights">View Research Insights</a></p>
"""

def render_action_center(ac) -> str:
    """Render action center as an HTML page.

    PAPER-ONLY / DATA-ONLY. No live trading.
    """
    # Build warning categories HTML
    cat_html = ""
    if ac.warning_categories:
        cat_html += '<table><tr><th>Category</th><th>Count</th><th>Items</th></tr>'
        for cat, items in ac.warning_categories.items():
            if items:
                items_list = "<br>".join(html.escape(item) for item in items)
                cat_html += f'<tr><td><b>{_esc(cat.upper())}</b></td><td>{len(items)}</td><td>{items_list}</td></tr>'
        cat_html += '</table>'
    else:
        cat_html = '<p>No categorized warnings.</p>'

    # Blockers
    blockers_html = ""
    if ac.blockers:
        blockers_html += '<ul>'
        for b in ac.blockers:
            blockers_html += f'<li><b>{_esc(b)}</b></li>'
        blockers_html += '</ul>'
    else:
        blockers_html = '<p>None</p>'

    # Warnings
    warnings_html = ""
    if ac.warnings:
        warnings_html += '<ul>'
        for w in ac.warnings:
            warnings_html += f'<li>{_esc(w)}</li>'
        warnings_html += '</ul>'
    else:
        warnings_html = '<p>None</p>'

    # Action items helpers
    def _items_html(items, color="#06c"):
        if not items:
            return '<p>None</p>'
        out = f'<ul>'
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
        outputs_html = '<p>None yet</p>'

    # Next safe commands
    commands_html = ""
    if ac.next_safe_commands:
        commands_html += '<ul>'
        for cmd in ac.next_safe_commands:
            commands_html += f'<li><code>{_esc(cmd)}</code></li>'
        commands_html += '</ul>'
    else:
        commands_html = '<p>None</p>'

    # Overall badge color
    overall_color = "#080" if ac.overall == "OK" else ("#a60" if ac.overall == "OK_WITH_WARNINGS" else "#c00")

    body = f"""
<h2>Action Center</h2>
<p><b>PAPER-ONLY / DATA-ONLY.</b> No live trading. No order submission.</p>
<p style="color:{overall_color}">Overall: {_esc(ac.overall)}</p>
<p>Mode: {_esc(ac.mode)} | Paper-only: {_esc(ac.paper_only)} | Data-only: {_esc(ac.data_only)} | No order submission: {_esc(ac.no_order_submission)}</p>
<p>{_esc(ac.disclaimer)}</p>
<h3>Readiness</h3>
<p><b>Score:</b> {_esc(ac.readiness_score if ac.readiness_score is not None else "N/A")}/100</p>
<p><b>Grade:</b> {_esc(ac.readiness_grade or "N/A")}</p>
<p><b>Status:</b> {_esc(ac.readiness_status or "N/A")}</p>
<p><b>Latest operator run:</b> {_esc(ac.latest_operator_run or "N/A")}</p>
<h3>Warning Categories</h3>
{cat_html}
<h4>Blockers ({len(ac.blockers)})</h4>
{blockers_html}
<h4>Warnings ({len(ac.warnings)})</h4>
{warnings_html}
<h3>Action Items</h3>
<h4>Readiness</h4>
{_items_html(ac.readiness_action_items)}
<h4>Workflow</h4>
{_items_html(ac.workflow_action_items)}
<h4>Briefing</h4>
{_items_html(ac.briefing_action_items)}
<h4>Dashboard</h4>
{_items_html(ac.dashboard_action_items)}
<h3>Latest Generated Outputs</h3>
{outputs_html}
<h3>Next Safe Commands</h3>
{commands_html}
<p><a href="/research-insights">View Research Insights</a></p>
<p>Reminder: reports/logs/local outputs should not be committed.<br>
This tool does not approve or enable live trading.<br>
No broker calls. No live network. No credential prompts.<br>
No actual email send. No actual Telegram send. No cron install.</p>
"""
    return wrap_html("Action Center", body)

def render_research_insights(summary) -> str:
    """Render research insights as an HTML page.

    PAPER-ONLY / DATA-ONLY. No live trading. Not financial advice.
    """
    # Strategy table
    strat_rows = ""
    if summary.strategies:
        for s in summary.strategies:
            color = {
                "candidate_for_further_paper_testing": "#080",
                "monitor_in_paper_mode": "#06c",
                "needs_more_data": "#a60",
                "inconclusive": "#888",
                "weak_paper_metrics": "#c00",
            }.get(s.classification, "#888")
            strat_rows += f"""
<tr>
  <td>{_esc(s.name)}</td>
  <td style="color:{color}">{_esc(s.classification)}</td>
  <td>{_esc(s.reason)}</td>
  <td>{_esc(s.score) if s.score is not None else "N/A"}</td>
  <td>{_esc(s.sharpe_metric) if s.sharpe_metric is not None else "N/A"}</td>
  <td>{_esc(s.win_rate_metric) if s.win_rate_metric is not None else "N/A"}</td>
  <td>{_esc(s.drawdown_metric) if s.drawdown_metric is not None else "N/A"}</td>
  <td>{_esc(s.sample_size) if s.sample_size is not None else "N/A"}</td>
</tr>
"""
    else:
        strat_rows = '<tr><td colspan="8">No research outputs found yet</td></tr>'

    # Top candidates
    top_html = ""
    if summary.top_candidates:
        top_html += "<ul>"
        for c in summary.top_candidates:
            top_html += f"<li>{_esc(c)}</li>"
        top_html += "</ul>"
    else:
        top_html = "<p>None</p>"

    # Weak candidates
    weak_html = ""
    if summary.weak_candidates:
        weak_html += "<ul>"
        for c in summary.weak_candidates:
            weak_html += f"<li>{_esc(c)}</li>"
        weak_html += "</ul>"
    else:
        weak_html = "<p>None</p>"

    # Inconclusive
    inconclusive_html = ""
    if summary.inconclusive:
        inconclusive_html += "<ul>"
        for c in summary.inconclusive:
            inconclusive_html += f"<li>{_esc(c)}</li>"
        inconclusive_html += "</ul>"
    else:
        inconclusive_html = "<p>None</p>"

    # Warnings
    warnings_html = ""
    if summary.warnings:
        warnings_html += "<ul>"
        for w in summary.warnings:
            warnings_html += f"<li>{_esc(w)}</li>"
        warnings_html += "</ul>"
    else:
        warnings_html = "<p>None</p>"

    # Data quality notes
    dq_html = ""
    if summary.data_quality_notes:
        dq_html += "<ul>"
        for note in summary.data_quality_notes:
            dq_html += f"<li>{_esc(note)}</li>"
        dq_html += "</ul>"
    else:
        dq_html = "<p>None</p>"

    # Next safe commands
    commands_html = ""
    if summary.next_safe_commands:
        commands_html += "<ul>"
        for cmd in summary.next_safe_commands:
            commands_html += f"<li><code>{_esc(cmd)}</code></li>"
        commands_html += "</ul>"
    else:
        commands_html = "<p>None</p>"

    body = f"""
<h2>Research Insights</h2>
<p><b>PAPER-ONLY / DATA-ONLY.</b> No live trading. No order submission.</p>
<p><b>Not financial advice.</b> This does not approve or enable live trading. This does not guarantee performance.</p>
<p>Generated: {_esc(summary.generated_at)} | Sources: {len(summary.source_paths)}</p>
<h3>Strategy Comparison</h3>
<table>
  <tr>
    <th>Name</th>
    <th>Classification</th>
    <th>Reason</th>
    <th>Score</th>
    <th>Sharpe</th>
    <th>Win Rate</th>
    <th>Drawdown</th>
    <th>Sample Size</th>
  </tr>
  {strat_rows}
</table>
<h3>Top Candidates (further paper testing)</h3>
{top_html}
<h3>Weak Candidates (avoid for now)</h3>
{weak_html}
<h3>Inconclusive / Needs More Data</h3>
{inconclusive_html}
<h3>Warnings</h3>
{warnings_html}
<h3>Data Quality Notes</h3>
{dq_html}
<h3>Next Safe Commands</h3>
{commands_html}
<p><a href="/">Home</a> | <a href="/operator">Operator Status</a> | <a href="/action-center">Action Center</a></p>
<p>Reminder: reports/logs/local outputs should not be committed.<br>
This tool does not approve or enable live trading.<br>
No broker calls. No live network. No credential prompts.<br>
No actual email send. No actual Telegram send. No cron install.</p>
"""
    return wrap_html("Research Insights", body)
