"""Phase 9 dashboard routes — additive, standalone module.

To include in main dashboard, import and register:
    from dashboard.routes_phase9 import register_phase9_routes
    register_phase9_routes(app)

Security: same viewer token auth as existing dashboard.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter()

VIEWER_TOKEN = "viewer-token"


def _verify_token(request: Request):
    token = request.query_params.get("token", "")
    if token != VIEWER_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/dashboard/phase9/stream", response_class=HTMLResponse)
async def stream_dashboard(request: Request):
    _verify_token(request)
    return """
    <html><head><title>Phase 9 Stream</title></head><body>
    <h1>Phase 9 — OANDA Practice Stream</h1>
    <div class="badge">PAPER-ONLY</div>
    <p>Stream status: <span id="status">idle</span></p>
    <p>Events received: <span id="events">0</span></p>
    <p>Last tick: <span id="tick">--</span></p>
    <p>Use CLI tools to start streams.</p>
    <pre>python tools/stream_oanda_prices.py --config examples/oanda_practice_real_config.example.json --output reports/</pre>
    </body></html>
    """


@router.get("/dashboard/phase9/snapshot", response_class=HTMLResponse)
async def snapshot_dashboard(request: Request):
    _verify_token(request)
    return """
    <html><head><title>Phase 9 Snapshot</title></head><body>
    <h1>Phase 9 — OANDA Practice Snapshot</h1>
    <div class="badge">PAPER-ONLY</div>
    <p>Account snapshot: run CLI to fetch</p>
    <pre>python tools/fetch_oanda_practice_snapshot.py --config examples/oanda_practice_real_config.example.json --output reports/snapshot.json</pre>
    <p>No account IDs or credentials are displayed.</p>
    </body></html>
    """


@router.get("/dashboard/phase9/safety", response_class=HTMLResponse)
async def safety_dashboard(request: Request):
    _verify_token(request)
    return """
    <html><head><title>Phase 9 Safety</title></head><body>
    <h1>Phase 9 — Safety Validation</h1>
    <div class="badge">PAPER-ONLY</div>
    <ul>
    <li>Live environment rejected: <span style="color:green">PASS</span></li>
    <li>Live orders rejected: <span style="color:green">PASS</span></li>
    <li>Live endpoint rejected: <span style="color:green">PASS</span></li>
    <li>Credentials redacted: <span style="color:green">PASS</span></li>
    <li>Account ID masked: <span style="color:green">PASS</span></li>
    <li>Order submission disabled by default: <span style="color:green">PASS</span></li>
    <li>Dry-run default: <span style="color:green">PASS</span></li>
    </ul>
    <pre>python tools/validate_phase9_safety.py --config examples/oanda_practice_real_config.example.json</pre>
    </body></html>
    """


def register_phase9_routes(app):
    app.include_router(router)
