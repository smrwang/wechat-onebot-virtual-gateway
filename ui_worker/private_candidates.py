"""Fail-closed discovery of approved private-chat candidates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PrivateCandidate:
    user_id: str
    fingerprint: str
    row: int


def find_private_candidates(
    rows: list[dict[str, Any]],
    registry: dict[str, dict[str, str]],
    previous: dict[str, dict[str, str]],
) -> list[PrivateCandidate]:
    candidates: list[PrivateCandidate] = []
    for row_index, row in enumerate(rows):
        fingerprint = str(row.get("fingerprint", ""))
        binding = registry.get(fingerprint)
        if binding is None or not bool(row.get("unread")) or bool(row.get("pinned")) or bool(row.get("folded")):
            continue
        now = {"preview": str(row.get("preview", "")), "timestamp": str(row.get("timestamp", ""))}
        if previous.get(fingerprint) == now:
            continue
        user_id = str(binding.get("user_id", ""))
        if user_id:
            candidates.append(PrivateCandidate(user_id, fingerprint, row_index))
    return candidates
