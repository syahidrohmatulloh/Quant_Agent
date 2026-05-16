"""BAPPEBTI broker registry metadata."""
from typing import Dict, Any, List

BAPPEBTI_BROKERS: List[Dict[str, Any]] = [
    {
        "broker_id": "mifx",
        "display_name": "MIFX / Monex Investindo Futures",
        "legal_check_url": "https://www.bappebti.go.id/id/regulasi/pialang_berjangka/",
        "bappebti_registered": True,
    },
    {
        "broker_id": "gkinvest",
        "display_name": "GKInvest / Global Kapital Investama Berjangka",
        "legal_check_url": "https://www.bappebti.go.id/id/regulasi/pialang_berjangka/",
        "bappebti_registered": True,
    },
    {
        "broker_id": "hsb",
        "display_name": "HSB Investasi",
        "legal_check_url": "https://www.bappebti.go.id/id/regulasi/pialang_berjangka/",
        "bappebti_registered": True,
    },
    {
        "broker_id": "finex",
        "display_name": "Finex",
        "legal_check_url": "https://www.bappebti.go.id/id/regulasi/pialang_berjangka/",
        "bappebti_registered": True,
    },
    {
        "broker_id": "dupoin",
        "display_name": "Dupoin Futures",
        "legal_check_url": "https://www.bappebti.go.id/id/regulasi/pialang_berjangka/",
        "bappebti_registered": True,
    },
    {
        "broker_id": "maxco",
        "display_name": "Maxco Futures",
        "legal_check_url": "https://www.bappebti.go.id/id/regulasi/pialang_berjangka/",
        "bappebti_registered": True,
    },
    {
        "broker_id": "octa_id",
        "display_name": "Octa Investama Berjangka",
        "legal_check_url": "https://www.bappebti.go.id/id/regulasi/pialang_berjangka/",
        "bappebti_registered": True,
    },
    {
        "broker_id": "xtb_id",
        "display_name": "XTB Indonesia Berjangka",
        "legal_check_url": "https://www.bappebti.go.id/id/regulasi/pialang_berjangka/",
        "bappebti_registered": True,
    },
]


def get_bappebti_info(broker_id: str) -> Dict[str, Any]:
    for b in BAPPEBTI_BROKERS:
        if b["broker_id"] == broker_id:
            return b
    return {"broker_id": broker_id, "bappebti_registered": False, "legal_check_url": "https://www.bappebti.go.id/"}
