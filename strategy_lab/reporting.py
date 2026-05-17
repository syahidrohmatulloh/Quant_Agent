"""
Generate markdown or JSON report for strategy results.
Includes disclaimer. Paper-only.
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any


PAPER_DISCLAIMER = (
    "DISCLAIMER: This report is for educational and research purposes only. "
    "All strategies are paper-only and not guaranteed profitable. "
    "Past performance does not guarantee future results. "
    "No live trading is enabled."
)


class StrategyReportGenerator:
    def __init__(self, result: Dict[str, Any], config: Dict[str, Any], output_dir: str = "reports"):
        self.result = result
        self.config = config
        self.output_dir = output_dir

    def to_json(self, filename: str = "strategy_report.json") -> str:
        path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": PAPER_DISCLAIMER,
            "config": self.config,
            "result": self.result
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        return path

    def to_markdown(self, filename: str = "strategy_report.md") -> str:
        path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)
        lines = [
            "# Strategy Report",
            "",
            f"Generated: {datetime.now(timezone.utc).isoformat()}Z",
            "",
            f"> {PAPER_DISCLAIMER}",
            "",
            "## Configuration",
            ""
        ]
        for k, v in self.config.items():
            lines.append(f"- **{k}**: {v}")
        lines.extend(["", "## Results", ""])
        for k, v in self.result.items():
            if isinstance(v, list) and len(v) > 10:
                lines.append(f"- **{k}**: [{len(v)} items]")
            else:
                lines.append(f"- **{k}**: {v}")
        lines.extend(["", "---", "", "End of report"])
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path
