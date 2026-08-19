"""User-facing capability status for the conservative inbound roadmap."""
from __future__ import annotations

from pathlib import Path

from panel.config_api import private_inbound_beta_enabled


def private_inbound_status(beta_path: Path | None = None) -> dict[str, object]:
    beta_enabled = private_inbound_beta_enabled(beta_path) if beta_path is not None else False
    return {
        "mode": "experimental_private_only",
        "enabled": beta_enabled,
        "beta_enabled": beta_enabled,
        "requires_unpinned_unfolded_inbox": True,
        "group_inbound": False,
        "mentions": False,
    }
