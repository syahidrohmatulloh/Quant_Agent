"""
Phase 14 + 25 + 26 + 27 + 28 + 29 + 30 dashboard routes.
FastAPI router with all read-only dashboard pages.
No live trading. No order submission. No broker calls.
Phase 25: adds /action-center route.
Phase 26: adds /research-insights route.
Phase 27: adds /paper-runtime route.
Phase 28: adds /data-quality route.
Phase 29: adds /paper-broker route.
Phase 30: adds /release-candidate route.
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

from dashboard.data_access import (
    list_datasets,
    get_dataset_detail,
    list_experiment_configs,
    get_experiment_config_preview,
    list_experiment_history,
    get_latest_dashboard_json,
    list_reports,
    get_report_detail,
    get_home_status,
)
from dashboard.templates import (
    render_home,
    render_datasets,
    render_dataset_detail,
    render_experiment_configs,
    render_experiment_run_preview,
    render_experiment_history,
    render_latest_dashboard,
    render_reports,
    render_report_detail,
    render_operator_status,
    render_action_center,
    render_research_insights,
    render_paper_runtime,
    render_data_quality,
    render_paper_broker,
    render_release_candidate,
)
from dashboard.safety import safe_dataset_id, safe_report_id

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    status = get_home_status()
    return HTMLResponse(content=render_home(status))

@router.get("/datasets", response_class=HTMLResponse)
async def datasets(request: Request):
    datasets = list_datasets()
    return HTMLResponse(content=render_datasets(datasets))

@router.get("/datasets/{dataset_id}", response_class=HTMLResponse)
async def dataset_detail(request: Request, dataset_id: str):
    safe_id = safe_dataset_id(dataset_id)
    vm = get_dataset_detail(safe_id)
    if vm is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return HTMLResponse(content=render_dataset_detail(vm))

@router.get("/experiments/configs", response_class=HTMLResponse)
async def experiment_configs(request: Request):
    configs = list_experiment_configs()
    return HTMLResponse(content=render_experiment_configs(configs))

@router.get("/experiments/run", response_class=HTMLResponse)
async def experiment_run(request: Request, config: str = Query(...)):
    try:
        preview = get_experiment_config_preview(config)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Config error: {e}")
    return HTMLResponse(content=render_experiment_run_preview(preview, config))

@router.get("/experiments/history", response_class=HTMLResponse)
async def experiment_history(request: Request):
    history = list_experiment_history()
    return HTMLResponse(content=render_experiment_history(history))

@router.get("/dashboard/latest", response_class=HTMLResponse)
async def latest_dashboard(request: Request):
    data = get_latest_dashboard_json()
    return HTMLResponse(content=render_latest_dashboard(data))

@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request):
    reports = list_reports()
    return HTMLResponse(content=render_reports(reports))

@router.get("/reports/{report_id}", response_class=HTMLResponse)
async def report_detail(request: Request, report_id: str):
    safe_id = safe_report_id(report_id)
    content = get_report_detail(safe_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return HTMLResponse(content=render_report_detail(safe_id, content))

@router.get("/health")
async def health():
    return JSONResponse(content={
        "ok": True,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
    })

@router.get("/operator", response_class=HTMLResponse)
def operator_status_page(request: Request) -> HTMLResponse:
    from dashboard.data_access import get_project_root
    return HTMLResponse(render_operator_status(get_project_root(), {}))

@router.get("/action-center", response_class=HTMLResponse)
def action_center_page(request: Request) -> HTMLResponse:
    """Action center page: categorized warnings, blockers, action items.

    PAPER-ONLY / DATA-ONLY. No live trading.
    """
    from dashboard.data_access import get_project_root
    from local_app.app_config import load_config
    from local_app.action_center import build_operator_action_center

    project_root = get_project_root()
    config_path = project_root / "examples" / "local_app_config.example.json"
    config = {}
    if config_path.exists():
        try:
            config = load_config(config_path)
        except Exception:
            pass
    ac = build_operator_action_center(config, project_root, config_path=config_path, allow_missing=True)
    return HTMLResponse(render_action_center(ac))

@router.get("/research-insights", response_class=HTMLResponse)
def research_insights_page(request: Request) -> HTMLResponse:
    """Research insights page: strategy comparison, classifications, warnings.

    PAPER-ONLY / DATA-ONLY. No live trading. Not financial advice.
    """
    from dashboard.data_access import get_project_root
    from local_app.app_config import load_config
    from research_insights.insight_builder import build_research_insights

    project_root = get_project_root()
    config_path = project_root / "examples" / "research_analytics_config.example.json"
    config = {}
    if config_path.exists():
        try:
            config = load_config(config_path)
        except Exception:
            pass
    summary = build_research_insights(project_root, config=config, allow_missing=True)
    return HTMLResponse(render_research_insights(summary))

@router.get("/paper-runtime", response_class=HTMLResponse)
def paper_runtime_page(request: Request) -> HTMLResponse:
    """Paper runtime monitoring page: session journal, signals, decisions, risk.

    PAPER-ONLY / DATA-ONLY. No live trading. Not financial advice.
    """
    from dashboard.data_access import get_project_root
    from local_app.app_config import load_config
    from paper_runtime.session_journal import build_paper_runtime_session

    project_root = get_project_root()
    config_path = project_root / "examples" / "local_app_config.example.json"
    config = {}
    if config_path.exists():
        try:
            config = load_config(config_path)
        except Exception:
            pass
    session = build_paper_runtime_session(project_root, config=config, allow_missing=True)
    return HTMLResponse(render_paper_runtime(session))

@router.get("/data-quality", response_class=HTMLResponse)
def data_quality_page(request: Request) -> HTMLResponse:
    """Data quality center page: scan market data CSVs for quality issues.

    PAPER-ONLY / DATA-ONLY. No live trading. Not financial advice.
    """
    from dashboard.data_access import get_project_root
    from local_app.app_config import load_config
    from data_quality.quality_report import build_data_quality_report, DataQualityReport

    project_root = get_project_root()
    config_path = project_root / "examples" / "market_data_import_config.example.json"
    config = {}
    if config_path.exists():
        try:
            config = load_config(config_path)
        except Exception:
            pass

    if not config:
        empty_report = DataQualityReport()
        empty_report.warnings.append("No market data import config found. Create examples/market_data_import_config.example.json")
        empty_report.status = "WARN"
        return HTMLResponse(render_data_quality(empty_report))

    report = build_data_quality_report(project_root, config=config, allow_missing=True)
    return HTMLResponse(render_data_quality(report))

@router.get("/paper-broker", response_class=HTMLResponse)
def paper_broker_page(request: Request) -> HTMLResponse:
    """Paper broker readiness page: adapter validation, config safety, connectivity simulation.

    PAPER-ONLY / DATA-ONLY. No live trading. Not financial advice.
    """
    from dashboard.data_access import get_project_root
    from local_app.app_config import load_config
    from paper_broker.readiness import build_paper_broker_readiness

    project_root = get_project_root()
    config_path = project_root / "examples" / "local_app_config.example.json"
    config = {}
    if config_path.exists():
        try:
            config = load_config(config_path)
        except Exception:
            pass

    report = build_paper_broker_readiness(project_root, config=config, allow_missing=True)
    return HTMLResponse(render_paper_broker(report))

@router.get("/release-candidate", response_class=HTMLResponse)
def release_candidate_page(request: Request) -> HTMLResponse:
    """Local MVP release candidate page: final readiness checks and demo safety.

    PAPER-ONLY / DATA-ONLY. No live trading. Not financial advice.
    """
    from dashboard.data_access import get_project_root
    from local_app.app_config import load_config
    from release_candidate.checklist import (
        build_release_candidate_report,
        load_latest_release_candidate_report,
    )

    project_root = get_project_root()
    config_path = project_root / "examples" / "local_app_config.example.json"
    config = {}
    if config_path.exists():
        try:
            config = load_config(config_path)
        except Exception:
            pass

    # Try to load existing report first
    report = load_latest_release_candidate_report(project_root, config=config)
    if report is None:
        # Build safe in-memory report
        report = build_release_candidate_report(project_root, config=config, allow_missing=True)
    return HTMLResponse(render_release_candidate(report))
