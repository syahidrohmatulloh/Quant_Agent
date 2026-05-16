
from typing import Dict, Any

class SignalRouter:
    def __init__(self, paper_only: bool = True):
        self.paper_only = paper_only

    def route(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        if not signal.get("generated"):
            return {"routed": False, "destination": None, "reason": "Signal not generated"}
        if self.paper_only:
            return {
                "routed": True,
                "destination": "paper",
                "signal": signal,
                "reason": "Paper-only mode"
            }
        return {
            "routed": True,
            "destination": "paper",
            "signal": signal,
            "reason": "Default to paper"
        }
