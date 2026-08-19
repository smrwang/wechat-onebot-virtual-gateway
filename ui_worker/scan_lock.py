"""Serialize X11 screenshot and Copy operations across HTTP poll requests."""
from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def scan_once_or_empty(lock: threading.Lock, work: Callable[[], list[T]]) -> list[T]:
    if not lock.acquire(blocking=False):
        return []
    try:
        return work()
    finally:
        lock.release()
