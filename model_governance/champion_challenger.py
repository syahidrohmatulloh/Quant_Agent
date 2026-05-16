
from typing import Dict, Any, Optional, List
from research_pipeline.model_registry import ModelRegistry, ModelEntry

class ChampionChallenger:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def compare(self, champion_id: str, challenger_id: str,
                metric_key: str = "accuracy") -> Dict[str, Any]:
        champ = self.registry.get(champion_id)
        chall = self.registry.get(challenger_id)
        if not champ or not chall:
            return {"error": "One or both models not found"}
        champ_metric = champ.metrics.get(metric_key, 0)
        chall_metric = chall.metrics.get(metric_key, 0)
        winner = challenger_id if chall_metric > champ_metric else champion_id
        return {
            "champion_id": champion_id,
            "challenger_id": challenger_id,
            "metric": metric_key,
            "champion_score": champ_metric,
            "challenger_score": chall_metric,
            "winner": winner,
            "recommendation": "promote challenger" if winner == challenger_id else "keep champion"
        }

    def get_champion(self) -> Optional[ModelEntry]:
        return self.registry.get_latest_approved()
