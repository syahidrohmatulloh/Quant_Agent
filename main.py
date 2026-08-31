import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from core.auth import get_role, require_role
from core.paper_broker import PaperBroker
from core.risk import RiskManager
from storage.db import SQLiteStore
from storage.audit import AuditLogger
from api.routes import router
from dashboard.routes_dashboard import router as dashboard_router
import uuid
from datetime import datetime, timezone

app = FastAPI(title="Quant Platform API")

app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")
app.include_router(router)
app.include_router(dashboard_router)

broker = PaperBroker(
    balance=float(os.getenv("PAPER_INITIAL_BALANCE", "100000")),
    commission_per_lot=float(os.getenv("PAPER_COMMISSION_PER_LOT", "7.0")),
    slippage_pips=float(os.getenv("PAPER_SLIPPAGE_PIPS", "0.5")),
    leverage=float(os.getenv("PAPER_LEVERAGE", "100.0"))
)
store = SQLiteStore(os.getenv("QUANT_SQLITE_PATH", "./data/quant_platform.db"))
audit = AuditLogger(os.getenv("AUDIT_JSONL_PATH", "./data/audit.jsonl"))
rm = RiskManager()

class OrderRequest(BaseModel):
    symbol: str
    direction: str
    volume: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    reason: Optional[str] = "manual"

@app.post("/manual/order")
async def manual_order(req: OrderRequest, token: str = Header(...)):
    role = get_role(token)
    if role not in {"operator", "admin"}:
        raise HTTPException(status_code=403, detail="Operator or admin role required")
    request_id = str(uuid.uuid4())
    audit.log("manual_order_requested", request_id, role, role, req.model_dump())

    decision = rm.evaluate(req.symbol, req.direction, req.volume)
    audit.log("risk_decision_created", request_id, role, role, {
        "risk_decision_id": decision.risk_decision_id,
        "allowed": decision.allowed
    })

    if not decision.allowed:
        raise HTTPException(status_code=400, detail="Risk check failed")

    price = 1.10025
    oid, pid = broker.open_position(req.symbol, req.direction, req.volume, price, req.sl, req.tp)

    order_record = {
        "order_id": str(uuid.uuid4()),
        "request_id": request_id,
        "idempotency_key": f"manual:{role}:{req.symbol}:{req.direction}:{datetime.now(timezone.utc).isoformat()}",
        "signal_id": None,
        "strategy_id": None,
        "strategy_version": None,
        "model_version": None,
        "source": "manual",
        "symbol": req.symbol,
        "direction": req.direction,
        "volume": req.volume,
        "entry_price": price,
        "sl": req.sl,
        "tp": req.tp,
        "status": "open",
        "broker_order_id": oid,
        "broker_position_id": pid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    store.insert_order(order_record)

    audit.log("order_created", request_id, role, role, {
        "order_id": order_record["order_id"],
        "position_id": pid,
        "broker_order_id": oid,
        "broker_position_id": pid
    })

    return {
        "status": "accepted",
        "simulated": True,
        "request_id": request_id,
        "order_id": order_record["order_id"],
        "position_id": pid,
        "broker_order_id": oid,
        "broker_position_id": pid,
        "risk_decision_id": decision.risk_decision_id,
        "error": None,
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
