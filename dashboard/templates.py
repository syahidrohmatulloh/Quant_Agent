"""
HTML template rendering for the Phase 14 dashboard.
Uses inline CSS only. No external CDN. Escapes all dynamic content.
Phase 25: adds action center page and fixes operator status rendering.
Phase 26: adds research insights page.
Phase 27: adds paper runtime page.
Phase 28: adds data quality page.
Phase 29: adds paper broker page.
"""
from pathlib import Path
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
<p><a href="/operator">Operator Status</a> | <a href="/action-center">Action Center</a> | <a href="/research-insights">Research Insights</a> | <a href="/paper-runtime">Paper Runtime</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
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
<thead>
<tr><th>Filename</th><th>Symbol</th><th>Timeframe</th><th>Source</th><th>Rows</th><th>Status</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
<p><a href="/">Home</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
"""
    return wrap_html("Datasets", body)

def render_dataset_detail(vm: DatasetViewModel) -> str:
    first_ts = getattr(vm, "first_timestamp", None) or "N/A"
    last_ts = getattr(vm, "last_timestamp", None) or "N/A"
    sample = getattr(vm, "sample_last_5", [])
    sample_html = ""
    if sample:
        sample_html += '<h3>Sample Last 5 Bars</h3><pre>'
        for row in sample:
            sample_html += html.escape(str(row)) + "\n"
        sample_html += '</pre>'
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
<p><a href="/datasets">Back to Datasets</a> | <a href="/">Home</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
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
<p><a href="/">Home</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
"""
    return wrap_html("Experiment Configs", body)

def render_experiment_run_preview(preview: Dict[str, Any], config_path: str) -> str:
    symbols = ", ".join(preview.get("symbols", []))
    strategies = ", ".join(preview.get("strategies", []))
    missing = preview.get("missing_csv_warnings", [])
    missing_html = ""
    if missing:
        missing_html = "<h3>Missing CSV Warnings</h3>\n<ul>\n"
        for m in missing:
            missing_html += f"<li>{_esc(m)}</li>\n"
        missing_html += "</ul>\n"
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
<p><a href="/">Home</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
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
{f'<a href="{_esc(h.result_path)}">Result</a>' if h.result_path else ""}
{f'<a href="{_esc(h.dashboard_json_path)}">JSON</a>' if h.dashboard_json_path else ""}
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
<p><a href="/">Home</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
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
    body += """
</tbody>
</table>
<p><a href="/">Home</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
"""
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
<thead>
<tr><th>Title</th><th>Generated</th><th>Path</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
<p><a href="/">Home</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
"""
    return wrap_html("Reports", body)

def render_report_detail(report_id: str, content: str) -> str:
    escaped = _esc(content)
    body = f"""
<h2>Report: {_esc(report_id)}</h2>
<pre>{escaped}</pre>
<p><a href="/reports">Back to Reports</a> | <a href="/">Home</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
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
<p><a href="/paper-runtime">View Paper Runtime</a></p>
<p><a href="/data-quality">View Data Quality</a></p>
<p><a href="/paper-broker">View Paper Broker</a></p>
"""

def render_action_center(ac) -> str:
    """Render action center as an HTML page.

    PAPER-ONLY / DATA-ONLY. No live trading.
    """
    # Build warning categories HTML
    cat_html = ""
    if ac.warning_categories:
        cat_html += '<table><thead><tr><th>Category</th><th>Count</th><th>Items</th></tr></thead><tbody>'
        for cat, items in ac.warning_categories.items():
            if items:
                items_list = "<br>".join(html.escape(item) for item in items)
                cat_html += f'<tr><td><b>{_esc(cat.upper())}</b></td><td>{len(items)}</td><td>{items_list}</td></tr>'
        cat_html += '</tbody></table>'
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
<p>Overall: <span style="color:{overall_color}">{_esc(ac.overall)}</span></p>
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
<p><a href="/">Home</a> | <a href="/operator">Operator Status</a> | <a href="/research-insights">Research Insights</a> | <a href="/paper-runtime">Paper Runtime</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
<p>Reminder: reports/logs/local outputs should not be committed.</p>
<p>This tool does not approve or enable live trading.</p>
<p>No broker calls. No live network. No credential prompts.</p>
<p>No actual email send. No actual Telegram send. No cron install.</p>
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
<td>{_esc(s.classification)}</td>
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
            commands_html += f'<li><code>{_esc(cmd)}</code></li>'
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
<thead>
<tr><th>Name</th><th>Classification</th><th>Reason</th><th>Score</th><th>Sharpe</th><th>Win Rate</th><th>Drawdown</th><th>Sample Size</th></tr>
</thead>
<tbody>
{strat_rows}
</tbody>
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
<p><a href="/">Home</a> | <a href="/operator">Operator Status</a> | <a href="/action-center">Action Center</a> | <a href="/paper-runtime">Paper Runtime</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
<p>Reminder: reports/logs/local outputs should not be committed.</p>
<p>This tool does not approve or enable live trading.</p>
<p>No broker calls. No live network. No credential prompts.</p>
<p>No actual email send. No actual Telegram send. No cron install.</p>
"""
    return wrap_html("Research Insights", body)

def render_paper_runtime(session) -> str:
    """Render paper runtime monitoring page.

    PAPER-ONLY / DATA-ONLY. No live trading. Not financial advice.
    """
    # Workflow status badge
    wf_status = session.workflow_status or "unknown"
    wf_color = {
        "completed": "#080",
        "not_found": "#888",
        "no_steps": "#888",
        "in_progress": "#06c",
    }.get(wf_status, "#a60")
    if wf_status.startswith("failed"):
        wf_color = "#c00"
    elif wf_status.startswith("warnings"):
        wf_color = "#a60"

    # Signal summary
    sig_status = session.signal_summary.get("status", "N/A")
    sig_html = ""
    if sig_status == "available":
        sig_count = session.signal_summary.get("count", 0)
        sig_html += f"<p>Signals found: {sig_count}</p>"
        signals = session.signal_summary.get("signals", [])
        if signals:
            sig_html += "<ul>"
            for sig in signals[:10]:
                sig_html += f"<li>{_esc(str(sig))}</li>"
            sig_html += "</ul>"
    else:
        sig_html = "<p>No signal summary available yet.</p>"

    # Paper decision summary
    dec_status = session.paper_decision_summary.get("status", "N/A")
    dec_html = ""
    if dec_status == "available":
        dec_count = session.paper_decision_summary.get("count", 0)
        dec_html += f"<p>Paper decisions found: {dec_count}</p>"
    else:
        dec_html = "<p>No paper decision summary available yet.</p>"

    # Portfolio summary
    port_status = session.portfolio_summary.get("status", "N/A")
    port_html = ""
    if port_status == "available":
        pos_count = session.portfolio_summary.get("position_count", 0)
        port_html += f"<p>Positions: {pos_count}</p>"
        if session.portfolio_summary.get("source"):
            port_html += f"<p>Source: <code>{_esc(session.portfolio_summary['source'])}</code></p>"
    else:
        port_html = "<p>No portfolio summary available yet.</p>"

    # PnL summary
    pnl_status = session.pnl_summary.get("status", "N/A")
    pnl_html = ""
    if pnl_status == "available":
        if session.pnl_summary.get("source"):
            pnl_html += f"<p>Source: <code>{_esc(session.pnl_summary['source'])}</code></p>"
    else:
        pnl_html = "<p>No PnL summary available yet.</p>"

    # Exposure summary
    exp_status = session.exposure_summary.get("status", "N/A")
    exp_html = ""
    if exp_status == "available":
        if session.exposure_summary.get("source"):
            exp_html += f"<p>Source: <code>{_esc(session.exposure_summary['source'])}</code></p>"
    else:
        exp_html = "<p>No exposure summary available yet.</p>"

    # Risk warnings
    risk_html = ""
    if session.risk_warnings:
        risk_html += f"<p>Count: {len(session.risk_warnings)}</p>"
        for w in session.risk_warnings[:20]:
            risk_html += f"<p>{_esc(w)}</p>"
    else:
        risk_html = "<p>None</p>"

    # Generated outputs
    outputs_html = ""
    if session.generated_outputs:
        outputs_html += f"<p>Count: {len(session.generated_outputs)}</p>"
        outputs_html += "<ul>"
        for p in session.generated_outputs[:20]:
            outputs_html += f'<li><code>{_esc(p)}</code></li>'
        outputs_html += "</ul>"
        if len(session.generated_outputs) > 20:
            outputs_html += f"<p>... and {len(session.generated_outputs) - 20} more</p>"
    else:
        outputs_html = "<p>No paper runtime outputs found yet.</p>"

    # Warnings
    warnings_html = ""
    if session.warnings:
        warnings_html += f"<p>Count: {len(session.warnings)}</p>"
        warnings_html += "<ul>"
        for w in session.warnings[:20]:
            warnings_html += f"<li>{_esc(w)}</li>"
        warnings_html += "</ul>"
    else:
        warnings_html = "<p>None</p>"

    # Blockers
    blockers_html = ""
    if session.blockers:
        blockers_html += f"<p>Count: {len(session.blockers)}</p>"
        blockers_html += "<ul>"
        for b in session.blockers:
            blockers_html += f'<li><b>{_esc(b)}</b></li>'
        blockers_html += "</ul>"
    else:
        blockers_html = "<p>None</p>"

    # Next safe commands
    commands_html = ""
    if session.next_safe_commands:
        commands_html += "<ul>"
        for cmd in session.next_safe_commands:
            commands_html += f'<li><code>{_esc(cmd)}</code></li>'
        commands_html += "</ul>"
    else:
        commands_html = "<p>None</p>"

    body = f"""
<h2>Paper Runtime Session Monitor</h2>
<p><b>PAPER-ONLY / DATA-ONLY.</b> No live trading. No order submission.</p>
<p><b>Not financial advice.</b> This does not approve or enable live trading. This does not guarantee performance.</p>
<p>Session ID: <code>{_esc(session.session_id or "N/A")}</code></p>
<p>Generated: {_esc(session.generated_at or "N/A")}</p>
<p>Paper-only: {_esc(session.paper_only)} | Data-only: {_esc(session.data_only)} | No order submission: {_esc(session.no_order_submission)}</p>
<h3>Workflow Status</h3>
<p style="color:{wf_color}">{_esc(wf_status)}</p>
<p>Steps: {len(session.workflow_steps)}</p>
<h3>Signal Summary</h3>
{sig_html}
<h3>Paper Decision Summary</h3>
{dec_html}
<h3>Portfolio Summary</h3>
{port_html}
<h3>PnL Summary</h3>
{pnl_html}
<h3>Exposure Summary</h3>
{exp_html}
<h3>Risk Warnings</h3>
{risk_html}
<h3>Generated Outputs</h3>
{outputs_html}
<h3>Warnings</h3>
{warnings_html}
<h3>Blockers</h3>
{blockers_html}
<h3>Next Safe Commands</h3>
{commands_html}
<p><a href="/">Home</a> | <a href="/operator">Operator Status</a> | <a href="/action-center">Action Center</a> | <a href="/research-insights">Research Insights</a> | <a href="/data-quality">Data Quality</a> | <a href="/paper-broker">Paper Broker</a></p>
<p>Reminder: reports/logs/local outputs should not be committed.</p>
<p>This tool does not approve or enable live trading.</p>
<p>No broker calls. No live network. No credential prompts.</p>
<p>No actual email send. No actual Telegram send. No cron install.</p>
"""
    return wrap_html("Paper Runtime", body)

def render_data_quality(report) -> str:
    """Render data quality center as an HTML page.

    PAPER-ONLY / DATA-ONLY. No live trading. Not financial advice.
    """
    # File report rows
    file_rows = ""
    if report.file_summaries:
        for s in report.file_summaries:
            status_color = "#080" if s.status == "ok" else ("#c00" if s.status in ("missing", "malformed", "empty") else "#a60")
            status_text = s.status.upper()
            file_rows += f"""
<tr>
<td>{_esc(Path(s.path).name)}</td>
<td>{status_text}</td>
<td>{s.rows}</td>
<td>{s.columns}</td>
<td>{s.duplicate_timestamp_count}</td>
<td>{s.non_monotonic}</td>
<td>{"Yes" if s.missing_required_columns else "No"}</td>
<td>{s.zero_or_negative_price_count}</td>
<td>{s.invalid_ohlc_count}</td>
<td>{s.start_time or "N/A"}</td>
<td>{s.end_time or "N/A"}</td>
</tr>
"""
    else:
        file_rows = '<tr><td colspan="11">No files scanned</td></tr>'

    # Issues
    issues_html = ""
    if report.issues:
        issues_html += f"<p>Count: {len(report.issues)}</p>"
        issues_html += "<ul>"
        for issue in report.issues:
            severity_color = {"info": "#06c", "warning": "#a60", "blocker": "#c00"}.get(issue.severity, "#888")
            issues_html += f'<li>[{issue.severity.upper()}] {_esc(issue.category)}: {_esc(issue.message)}'
            if issue.suggested_action:
                issues_html += f" <i>Action: {_esc(issue.suggested_action)}</i>"
            issues_html += '</li>'
        issues_html += "</ul>"
    else:
        issues_html = "<p>None</p>"

    # Warnings
    warnings_html = ""
    if report.warnings:
        warnings_html += f"<p>Count: {len(report.warnings)}</p>"
        warnings_html += "<ul>"
        for w in report.warnings:
            warnings_html += f"<li>{_esc(w)}</li>"
        warnings_html += "</ul>"
    else:
        warnings_html = "<p>None</p>"

    # Blockers
    blockers_html = ""
    if report.blockers:
        blockers_html += f"<p>Count: {len(report.blockers)}</p>"
        blockers_html += "<ul>"
        for b in report.blockers:
            blockers_html += f'<li><b>{_esc(b)}</b></li>'
        blockers_html += "</ul>"
    else:
        blockers_html = "<p>None</p>"

    # Data quality notes
    notes_html = ""
    if report.data_quality_notes:
        notes_html += "<ul>"
        for note in report.data_quality_notes:
            notes_html += f"<li>{_esc(note)}</li>"
        notes_html += "</ul>"
    else:
        notes_html = "<p>None</p>"

    # Generated outputs
    outputs_html = ""
    if report.generated_outputs:
        outputs_html += "<ul>"
        for p in report.generated_outputs:
            outputs_html += f'<li><code>{_esc(p)}</code></li>'
        outputs_html += "</ul>"
    else:
        outputs_html = "<p>None yet</p>"

    # Next safe commands
    commands_html = ""
    if report.next_safe_commands:
        commands_html += "<ul>"
        for cmd in report.next_safe_commands:
            commands_html += f'<li><code>{_esc(cmd)}</code></li>'
        commands_html += "</ul>"
    else:
        commands_html = "<p>None</p>"

    # Status badge color
    status_color = {"OK": "#080", "WARN": "#a60", "BLOCKED": "#c00"}.get(report.status, "#888")

    body = f"""
<h2>Data Quality Center
<p>No files scanned. No market data import config found yet.</p></h2>
<p><b>PAPER-ONLY / DATA-ONLY.</b> No live trading. No order submission.</p>
<p><b>Not financial advice.</b> This does not approve or enable live trading. This does not guarantee performance.</p>
<p>Generated: {_esc(report.generated_at or "N/A")}</p>
<p>Status: <span style="color:{status_color}">{_esc(report.status)}</span></p>
<p>Paper-only: {_esc(report.paper_only)} | Data-only: {_esc(report.data_only)} | No order submission: {_esc(report.no_order_submission)}</p>
<h3>Summary</h3>
<p>Files scanned: {report.files_scanned}</p>
<h3>File Reports</h3>
<table>
<thead>
<tr><th>File</th><th>Status</th><th>Rows</th><th>Cols</th><th>Dupes</th><th>Non-Mono</th><th>Missing Cols</th><th>Zero/Neg</th><th>Invalid OHLC</th><th>Start</th><th>End</th></tr>
</thead>
<tbody>
{file_rows}
</tbody>
</table>
<h3>Issues</h3>
{issues_html}
<h3>Warnings</h3>
{warnings_html}
<h3>Blockers</h3>
{blockers_html}
<h3>Data Quality Notes</h3>
{notes_html}
<h3>Generated Outputs</h3>
{outputs_html}
<h3>Next Safe Commands</h3>
{commands_html}
<p><a href="/">Home</a> | <a href="/operator">Operator Status</a> | <a href="/action-center">Action Center</a> | <a href="/research-insights">Research Insights</a> | <a href="/paper-runtime">Paper Runtime</a> | <a href="/paper-broker">Paper Broker</a></p>
<p>Reminder: reports/logs/local outputs should not be committed.</p>
<p>This tool does not approve or enable live trading.</p>
<p>No broker calls. No live network. No credential prompts.</p>
<p>No actual email send. No actual Telegram send. No cron install.</p>
"""
    return wrap_html("Data Quality", body)

def render_paper_broker(report) -> str:
    """Render paper broker readiness as an HTML page.

    PAPER-ONLY / DATA-ONLY. No live trading. Not financial advice.
    """
    # Status badge color
    status_color = {"READY": "#080", "READY_WITH_WARNINGS": "#a60", "BLOCKED": "#c00"}.get(report.status, "#888")

    # Check rows
    check_rows = ""
    if report.checks:
        for c in report.checks:
            icon = "[PASS]" if c.status == "PASS" else ("[WARN]" if c.status == "WARN" else "[BLOCKED]")
            check_rows += f"""
<tr>
<td>{_esc(c.name)}</td>
<td>{_esc(c.status)}</td>
<td>{_esc(c.category)}</td>
<td>{_esc(c.message)}</td>
<td>{_esc(c.suggested_action)}</td>
</tr>
"""
    else:
        check_rows = '<tr><td colspan="5">No checks performed</td></tr>'

    # Warnings
    warnings_html = ""
    if report.warnings:
        warnings_html += f"<p>Count: {len(report.warnings)}</p>"
        warnings_html += "<ul>"
        for w in report.warnings:
            warnings_html += f"<li>{_esc(w)}</li>"
        warnings_html += "</ul>"
    else:
        warnings_html = "<p>None</p>"

    # Blockers
    blockers_html = ""
    if report.blockers:
        blockers_html += f"<p>Count: {len(report.blockers)}</p>"
        blockers_html += "<ul>"
        for b in report.blockers:
            blockers_html += f'<li><b>{_esc(b)}</b></li>'
        blockers_html += "</ul>"
    else:
        blockers_html = "<p>None</p>"

    # Generated outputs
    outputs_html = ""
    if report.generated_outputs:
        outputs_html += "<ul>"
        for p in report.generated_outputs:
            outputs_html += f'<li><code>{_esc(p)}</code></li>'
        outputs_html += "</ul>"
    else:
        outputs_html = "<p>None yet</p>"

    # Next safe commands
    commands_html = ""
    if report.next_safe_commands:
        commands_html += "<ul>"
        for cmd in report.next_safe_commands:
            commands_html += f'<li><code>{_esc(cmd)}</code></li>'
        commands_html += "</ul>"
    else:
        commands_html = "<p>None</p>"

    # No config message
    no_config_msg = ""
    if not report.checks or all(c.category == "config" and c.status in ("WARN", "BLOCKED") for c in report.checks if c.name == "config_exists"):
        no_config_msg = '<p><b>No paper broker config found yet.</b> Run the CLI tool to generate a readiness report.</p>'

    body = f"""
<h2>Paper Broker Readiness</h2>
<p><b>PAPER-ONLY / DATA-ONLY.</b> No live trading. No order submission.</p>
<p><b>Not financial advice.</b> This does not approve or enable live trading. This does not guarantee performance.</p>
<p>Generated: {_esc(report.generated_at or "N/A")}</p>
<p>Status: <span style="color:{status_color}">{_esc(report.status)}</span></p>
<p>Broker: {_esc(report.broker_name or "N/A")} | Mode: {_esc(report.mode or "N/A")}</p>
<p>Config: <code>{_esc(report.config_path or "N/A")}</code></p>
{no_config_msg}
<h3>Checks</h3>
<table>
<thead>
<tr><th>Name</th><th>Status</th><th>Category</th><th>Message</th><th>Suggested Action</th></tr>
</thead>
<tbody>
{check_rows}
</tbody>
</table>
<h3>Warnings</h3>
{warnings_html}
<h3>Blockers</h3>
{blockers_html}
<h3>Generated Outputs</h3>
{outputs_html}
<h3>Next Safe Commands</h3>
{commands_html}
<p><a href="/">Home</a> | <a href="/operator">Operator Status</a> | <a href="/action-center">Action Center</a> | <a href="/research-insights">Research Insights</a> | <a href="/paper-runtime">Paper Runtime</a> | <a href="/data-quality">Data Quality</a></p>
<p>Reminder: reports/logs/local outputs should not be committed.</p>
<p>This tool does not approve or enable live trading.</p>
<p>No broker calls. No live network. No credential prompts.</p>
<p>No actual email send. No actual Telegram send. No cron install.</p>
"""
    return wrap_html("Paper Broker Readiness", body)
