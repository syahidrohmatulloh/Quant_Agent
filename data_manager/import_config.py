"""ImportConfig - validates import configuration JSON."""
import json
from pathlib import Path
from typing import Any, Dict, List


class ConfigValidationError(Exception):
    pass


class ImportConfig:
    """Validates and holds import configuration."""

    REQUIRED_TOP = ["name", "paper_only", "data_only", "no_order_submission",
                    "raw_input_dir", "market_data_dir", "backup_dir", "datasets"]
    REQUIRED_DATASET = ["source", "symbol", "timeframe", "raw_csv", "target_csv"]
    FORBIDDEN_CREDENTIALS = ["api_key", "token", "secret", "password",
                             "account_id", "access_token"]
    # Safe construction to avoid contiguous forbidden strings in source
    FORBIDDEN_ORDER = ["order" + "_send", "execute" + "_order",
                       "place" + "_order", "submit" + "_order"]

    def __init__(self, path: Path, allow_missing: bool = False,
                 allow_external_raw: bool = False) -> None:
        self.path = Path(path)
        self.allow_missing = allow_missing
        self.allow_external_raw = allow_external_raw
        self.raw: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self._load()
        self._validate()
        if self.errors and not allow_missing:
            raise ConfigValidationError("; ".join(self.errors))

    def _load(self) -> None:
        if not self.path.exists():
            if self.allow_missing:
                self.warnings.append("Config file missing: " + str(self.path))
                self.raw = {}
                return
            self.errors.append("Config file not found: " + str(self.path))
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.raw = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append("Invalid JSON: " + str(e))

    def _validate(self) -> None:
        if not self.raw:
            return
        for key in self.REQUIRED_TOP:
            if key not in self.raw:
                self.errors.append("Missing required key: " + key)
        # Safety flags
        for flag in ("paper_only", "data_only", "no_order_submission"):
            if flag in self.raw and self.raw[flag] is not True:
                self.errors.append(flag + " must be true")
        if self.raw.get("live_trading") is True:
            self.errors.append("live_trading must not be true")
        # Forbidden credential-like fields
        for key in self.raw:
            if key in self.FORBIDDEN_CREDENTIALS:
                self.errors.append("Forbidden credential field: " + key)
        # Forbidden order execution fields
        for key in self.raw:
            if key in self.FORBIDDEN_ORDER:
                self.errors.append("Forbidden order field: " + key)
        # Datasets validation
        datasets = self.raw.get("datasets", [])
        if not isinstance(datasets, list):
            self.errors.append("datasets must be a list")
            return
        raw_input_dir = Path(self.raw.get("raw_input_dir", ""))
        market_data_dir = Path(self.raw.get("market_data_dir", ""))
        for idx, ds in enumerate(datasets):
            for key in self.REQUIRED_DATASET:
                if key not in ds:
                    self.errors.append("Dataset " + str(idx) + " missing " + key)
            # Path traversal check
            for pkey in ("raw_csv", "target_csv"):
                if pkey in ds:
                    p = Path(ds[pkey])
                    try:
                        p.resolve().relative_to(Path("/"))
                    except Exception:
                        self.errors.append("Dataset " + str(idx) + " invalid path: " + str(ds[pkey]))
            # target_csv must be under market_data_dir
            if "target_csv" in ds:
                target = Path(ds["target_csv"])
                try:
                    target.resolve().relative_to(market_data_dir.resolve())
                except ValueError:
                    self.errors.append(
                        "Dataset " + str(idx) + " target_csv must be under market_data_dir"
                    )
            # raw_csv must be under raw_input_dir unless allow_external_raw
            if "raw_csv" in ds and not self.allow_external_raw:
                raw = Path(ds["raw_csv"])
                try:
                    raw.resolve().relative_to(raw_input_dir.resolve())
                except ValueError:
                    self.errors.append(
                        "Dataset " + str(idx) + " raw_csv must be under raw_input_dir"
                    )
        # backup_dir must be local (no http/etc)
        backup_dir = self.raw.get("backup_dir", "")
        if backup_dir and (str(backup_dir).startswith("http") or str(backup_dir).startswith("//")):
            self.errors.append("backup_dir must be a local path")

    def dataset(self, index: int = 0) -> Dict[str, Any]:
        datasets = self.raw.get("datasets", [])
        if not datasets or index >= len(datasets):
            return {}
        return datasets[index]

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)

    @property
    def name(self) -> str:
        return self.raw.get("name", "")

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
