"""Gate the current-active-chat scanner behind explicit Beta safety rules."""
from __future__ import annotations

from typing import Protocol

from ui_worker.active_beta_guard import approved_single_private_user


class ActiveScanner(Protocol):
    def scan(self, user_id: str) -> list[dict[str, str]]: ...


def poll_active_private_beta(beta_enabled: bool, registry: dict[str, dict[str, str]], scanner: ActiveScanner) -> list[dict[str, str]]:
    user_id = approved_single_private_user(registry)
    if not beta_enabled or user_id is None:
        return []
    return scanner.scan(user_id)
