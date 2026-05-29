"""
Paper portfolio state manager.
Local JSON state only. No real broker. No external execution.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PaperPortfolio:
    """Simulated paper portfolio backed by a local JSON file."""

    def __init__(self, state_path: str, cash_simulated: float = 100000.0):
        self.state_path = Path(state_path)
        self._cash_default = cash_simulated
        self._state = self._load_or_init()

    def _load_or_init(self) -> Dict[str, Any]:
        if self.state_path.exists():
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        now = _now_iso()
        return {
            "cash_simulated": self._cash_default,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "position_count": 0,
            "last_run_id": None,
            "created_at": now,
            "updated_at": now,
            "positions": {},
            "paper_only": True,
            "data_only": True,
            "no_order_submission": True,
        }

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2, default=str)

    def get_state(self) -> Dict[str, Any]:
        return self._state.copy()

    def update_positions(
        self,
        decisions: List[Dict[str, Any]],
        run_id: str,
    ) -> None:
        positions: Dict[str, Any] = {}
        gross = 0.0
        net = 0.0
        for d in decisions:
            if d.get("action") in ("PAPER_LONG", "PAPER_SHORT", "PAPER_NEUTRAL", "PAPER_HOLD"):
                sym = d.get("symbol")
                tf = d.get("timeframe")
                key = sym + "_" + tf if tf else sym
                side = "LONG" if d.get("action") == "PAPER_LONG" else (
                    "SHORT" if d.get("action") == "PAPER_SHORT" else "NEUTRAL"
                )
                weight = d.get("target_weight", 0.0)
                if side == "NEUTRAL":
                    weight = 0.0
                positions[key] = {
                    "symbol": sym,
                    "timeframe": tf,
                    "side": side,
                    "target_weight": weight,
                    "source_strategy_consensus": d.get("source_strategy_consensus", ""),
                    "confidence_label": d.get("confidence_label", "none"),
                    "updated_at": d.get("generated_at", _now_iso()),
                    "paper_only": True,
                }
                gross += abs(weight)
                net += weight if side == "LONG" else (-weight if side == "SHORT" else 0.0)

        self._state["positions"] = positions
        self._state["gross_exposure"] = round(gross, 6)
        self._state["net_exposure"] = round(net, 6)
        self._state["position_count"] = len(positions)
        self._state["last_run_id"] = run_id
        self._state["updated_at"] = _now_iso()
        self._save()

    def reset(self, confirm: bool = False) -> None:
        if not confirm:
            raise ValueError("Reset refused: --confirm-reset flag required.")
        now = _now_iso()
        self._state = {
            "cash_simulated": self._cash_default,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "position_count": 0,
            "last_run_id": None,
            "created_at": now,
            "updated_at": now,
            "positions": {},
            "paper_only": True,
            "data_only": True,
            "no_order_submission": True,
        }
        self._save()

    def summary(self) -> Dict[str, Any]:
        return {
            "cash_simulated": self._state["cash_simulated"],
            "gross_exposure": self._state["gross_exposure"],
            "net_exposure": self._state["net_exposure"],
            "position_count": self._state["position_count"],
            "last_run_id": self._state["last_run_id"],
            "updated_at": self._state["updated_at"],
            "paper_only": True,
            "data_only": True,
            "no_order_submission": True,
        }
