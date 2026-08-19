"""Guard the active-chat Beta scanner against ambiguous private identity."""
from __future__ import annotations


def approved_single_private_user(registry: dict[str, dict[str, str]]) -> str | None:
    users = {str(binding.get("user_id", "")) for binding in registry.values() if str(binding.get("user_id", ""))}
    return next(iter(users)) if len(users) == 1 else None
