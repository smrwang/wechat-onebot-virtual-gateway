"""Per-private-chat selection of unseen bubbles from visible overlap windows."""
from __future__ import annotations

from pathlib import Path

from ui_worker.bubble_overlap import new_bubble_keys
from ui_worker.private_cursor import PrivateCursor


class PrivateBubbleSelector:
    def __init__(self, path: Path) -> None:
        self.cursor = PrivateCursor(path)

    def baseline(self, conversation_id: str, bubble_keys: list[str]) -> list[str]:
        self.cursor.baseline(conversation_id, bubble_keys)
        return []

    def select(self, conversation_id: str, bubble_keys: list[str]) -> list[str]:
        state = self.cursor._conversation(conversation_id)
        previous = list(state.get("baseline", []))
        candidates = new_bubble_keys(previous, bubble_keys)
        state["baseline"] = list(bubble_keys)
        selected = [key for key in candidates if self.cursor.accept(conversation_id, "bubble", key)]
        self.cursor._save()
        return selected
