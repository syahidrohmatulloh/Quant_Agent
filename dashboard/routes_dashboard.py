
import os
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.auth import get_role, ROLES

router = APIRouter(prefix="/dashboard")

# Determine template directory relative to this file
_template_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=_template_dir)

DASHBOARD_AUTH_DISABLED = os.getenv("DASHBOARD_AUTH_DISABLED", "false").lower() == "true"

def _require_viewer(token: Optional[str] = None):
    if DASHBOARD_AUTH_DISABLED:
        return "viewer"
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    return get_role(token)

@router.get("/", response_class=HTMLResponse)
async def dashboard_index(request: Request, token: Optional[str] = Header(None)):
    _require_viewer(token)
    return templates.TemplateResponse(request, "index.html", {
        "mode": "paper",
        "time": "",
        "uptime": "",
        "health": "ok"
    })

@router.get("/positions", response_class=HTMLResponse)
async def dashboard_positions(request: Request, token: Optional[str] = Header(None)):
    _require_viewer(token)
    return templates.TemplateResponse(request, "positions.html", {
        "positions": [],
        "pnl": 0.0
    })

@router.get("/signals", response_class=HTMLResponse)
async def dashboard_signals(request: Request, token: Optional[str] = Header(None)):
    _require_viewer(token)
    return templates.TemplateResponse(request, "signals.html", {
        "signals": [],
        "rejected": []
    })

@router.get("/alerts", response_class=HTMLResponse)
async def dashboard_alerts(request: Request, token: Optional[str] = Header(None)):
    _require_viewer(token)
    return templates.TemplateResponse(request, "alerts.html", {
        "alerts": []
    })

@router.get("/models", response_class=HTMLResponse)
async def dashboard_models(request: Request, token: Optional[str] = Header(None)):
    _require_viewer(token)
    return templates.TemplateResponse(request, "models.html", {
        "approved": [],
        "candidate": [],
        "rejected": []
    })

@router.get("/backtests", response_class=HTMLResponse)
async def dashboard_backtests(request: Request, token: Optional[str] = Header(None)):
    _require_viewer(token)
    return templates.TemplateResponse(request, "backtests.html", {
        "reports": []
    })
