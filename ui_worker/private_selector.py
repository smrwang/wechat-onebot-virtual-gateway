"""Per-private-chat selection of unseen bubbles from visible overlap windows."""
from __future__ import annotations

from pathlib import Path

from ui_worker.bubble_overlap import new_bubble_keys
from ui_worker.private_cursor import PrivateCursor


class PrivateBubbleSelector:
    def __init__(self, path: Path) -> None:
        self.cursor = PrivateCursor(path)

    def has_baseline(self, conversation_id: str) -> bool:
        state = self.cursor._conversation(conversation_id)
        return bool(state.get("initialized")) or bool(state.get("baseline", []))

    def baseline(self, conversation_id: str, bubble_keys: list[str]) -> list[str]:
        self.cursor.baseline(conversation_id, bubble_keys)
        return []

    def candidates(self, conversation_id: str, bubble_keys: list[str]) -> list[str]:
        state = self.cursor._conversation(conversation_id)
        previous = list(state.get("baseline", []))
        return new_bubble_keys(previous, bubble_keys)

    def commit_visible(self, conversation_id: str, bubble_keys: list[str]) -> None:
        state = self.cursor._conversation(conversation_id)
        state["baseline"] = list(bubble_keys)
        self.cursor._save()

    def select(self, conversation_id: str, bubble_keys: list[str]) -> list[str]:
        selected = [key for key in self.candidates(conversation_id, bubble_keys) if self.cursor.accept(conversation_id, "bubble", key)]
        self.cursor._save()
        return selected
