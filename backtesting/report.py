
import json
import csv
import os
from datetime import datetime, timezone
from typing import Dict, List, Any

class ReportGenerator:
    def __init__(self, results: Dict[str, Any]):
        self.results = results

    def to_json(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)

    def to_csv(self, path: str) -> None:
        trades = self.results.get("trades", [])
        if not trades:
            return
        fieldnames = list(trades[0].keys())
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(trades)

    def to_markdown(self, path: str) -> None:
        lines = []
        lines.append("# Backtest Report")
        lines.append("")
        lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}Z")
        lines.append("")
        lines.append("## Summary")
        summary = self.results.get("summary", {})
        for key, value in summary.items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")
        lines.append("## Trades")
        trades = self.results.get("trades", [])
        lines.append(f"Total trades: {len(trades)}")
        lines.append("")
        if trades:
            lines.append("| # | Symbol | Direction | Entry | Exit | PnL |")
            lines.append("|---|--------|-----------|-------|------|-----|")
            for i, t in enumerate(trades, 1):
                lines.append(
                    f"| {i} | {t.get('symbol','')} | {t.get('direction','')} | "
                    f"{t.get('entry_price','')} | {t.get('exit_price','')} | {t.get('pnl','')} |"
                )
        lines.append("")
        lines.append("---")
        lines.append("End of report")
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
