"""Isolated experimental private inbound extraction endpoint logic."""
from __future__ import annotations

from typing import Protocol

from ui_worker.private_poll import build_private_event


class BubbleCopyRunner(Protocol):
    def copy_private_bubble(self, point: tuple[int, int]) -> str | None: ...


def experimental_private_event(driver: BubbleCopyRunner, user_id: str, point: tuple[int, int], bubble_key: str) -> dict[str, str] | None:
    text = driver.copy_private_bubble(point)
    return build_private_event(user_id, text or "", bubble_key)
