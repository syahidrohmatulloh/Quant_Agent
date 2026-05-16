from __future__ import annotations

import os
from typing import Dict


class EnvAuth:
    def __init__(self, api_key_env: str, api_secret_env: str | None = None):
        self.api_key_env = api_key_env
        self.api_secret_env = api_secret_env

    @property
    def api_key(self) -> str | None:
        return os.getenv(self.api_key_env) if self.api_key_env else None

    @property
    def api_secret(self) -> str | None:
        return os.getenv(self.api_secret_env) if self.api_secret_env else None

    def get_api_key(self) -> str | None:
        return self.api_key

    def get_api_secret(self) -> str | None:
        return self.api_secret

    def build_headers(self) -> Dict[str, str]:
        key = self.get_api_key()
        if not key:
            return {}
        return {"Authorization": f"Bearer {key}"}

    def has_credentials(self) -> bool:
        return bool(self.get_api_key())

    def is_configured(self) -> bool:
        return bool(self.get_api_key())

    def __repr__(self) -> str:
        key_status = "set" if self.get_api_key() else "missing"
        return f"EnvAuth(key_env={self.api_key_env}, key={key_status})"
