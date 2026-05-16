"""Phase 8 dashboard routes - additive, standalone module.

To include in main dashboard, import and register these routes:
    from dashboard.routes_phase8 import register_phase8_routes
    register_phase8_routes(app)

Security: same viewer token auth as existing dashboard.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter()

VIEWER_TOKEN = "viewer-token"  # Should match existing dashboard auth


def _verify_token(request: Request):
    token = request.query_params.get("token", "")
    if token != VIEWER_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/dashboard/broker", response_class=HTMLResponse)
async def broker_dashboard(request: Request):
    _verify_token(request)
    html = """
    <html><head><title>Broker Dashboard</title></head><body>
    <h1>Broker Health</h1>
    <div class="badge">PAPER-ONLY</div>
    <table>
    <tr><th>Broker</th><th>Environment</th><th>Healthy</th><th>Status</th></tr>
    <tr><td>OANDA</td><td>practice</td><td>Check CLI</td><td>paper-only</td></tr>
    <tr><td>Alpaca</td><td>paper</td><td>Check CLI</td><td>paper-only</td></tr>
    <tr><td>IBKR</td><td>paper</td><td>Check CLI</td><td>paper-only</td></tr>
    </table>
    <p>No secrets or credentials are displayed.</p>
    </body></html>
    """
    return html


@router.get("/dashboard/live-paper", response_class=HTMLResponse)
async def live_paper_dashboard(request: Request):
    _verify_token(request)
    html = """
    <html><head><title>Live Paper Session</title></head><body>
    <h1>Live Paper Session Status</h1>
    <div class="badge">PAPER-ONLY</div>
    <p>Session status: <span id="status">idle</span></p>
    <p>Last tick: <span id="tick">--</span></p>
    <p>Reconciliation: <span id="recon">--</span></p>
    <p>Last snapshot: <span id="snapshot">--</span></p>
    <p>Use CLI tools to start sessions.</p>
    </body></html>
    """
    return html


@router.get("/dashboard/reconciliation", response_class=HTMLResponse)
async def reconciliation_dashboard(request: Request):
    _verify_token(request)
    html = """
    <html><head><title>Reconciliation</title></head><body>
    <h1>Broker Reconciliation</h1>
    <div class="badge">PAPER-ONLY</div>
    <p>Run <code>python tools/reconcile_paper_broker.py</code> to generate reports.</p>
    <p>No account IDs or secrets are displayed.</p>
    </body></html>
    """
    return html


def register_phase8_routes(app):
    app.include_router(router)
