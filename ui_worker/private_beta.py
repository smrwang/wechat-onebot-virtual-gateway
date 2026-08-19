"""Shared persisted switch for the experimental private inbound path."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def private_inbound_beta_enabled(path: Path) -> bool:
    try:
        return json.loads(path.read_text()).get("enabled") is True
    except (FileNotFoundError, json.JSONDecodeError):
        return False


def apply_private_inbound_beta(path: Path, payload: dict[str, Any]) -> bool:
    enabled = payload.get("enabled")
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be a boolean")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"enabled": enabled}))
    os.replace(temporary, path)
    return enabled
