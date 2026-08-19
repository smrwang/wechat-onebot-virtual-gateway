"""Single-active-chat private inbound Beta scanner.

This intentionally supports only the already-open, operator-approved private chat.
It establishes a historical baseline on first scan and never publishes OCR text;
only verified Copy output is emitted.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ui_worker.private_poll import build_private_event
from ui_worker.private_selector import PrivateBubbleSelector


class ActiveBubbleRunner(Protocol):
    def read_active_bubbles(self) -> list[tuple[str, tuple[int, int]]]: ...
    def copy_private_bubble(self, point: tuple[int, int]) -> str | None: ...


class ActivePrivateBetaScanner:
    def __init__(self, cursor_path: Path, runner: ActiveBubbleRunner) -> None:
        self.selector = PrivateBubbleSelector(cursor_path)
        self.runner = runner

    def scan(self, user_id: str) -> list[dict[str, str]]:
        bubbles = self.runner.read_active_bubbles()
        keys = [key for key, _ in bubbles]
        if not self.selector.has_baseline(user_id):
            self.selector.baseline(user_id, keys)
            return []
        points = dict(bubbles)
        events: list[dict[str, str]] = []
        candidates = self.selector.candidates(user_id, keys)
        for key in candidates:
            point = points.get(key)
            if point is None:
                continue
            text = self.runner.copy_private_bubble(point)
            event = build_private_event(user_id, text or "", key)
            if event is not None and not self.selector.cursor.seen(user_id, event["text"], key) and self.selector.cursor.accept(user_id, event["text"], key):
                events.append(event)
        if not candidates or len(events) == len(candidates):
            self.selector.commit_visible(user_id, keys)
        return events
