"""Deterministic WeChat X11 driver boundary.

The runner is the only platform-specific layer. Production code can provide
an xdotool/tesseract runner; tests use a recording runner. No AI is involved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class X11Runner(Protocol):
    def open_search(self) -> None: ...
    def type_search(self, text: str) -> None: ...
    def capture_ocr(self) -> str: ...
    def click_search_result(self, search_key: str) -> None: ...
    def paste_and_send(self, text: str) -> None: ...
    def copy_bubble_text(self, point: tuple[int, int], menu_origin: tuple[int, int]) -> str | None: ...
    def read_active_bubbles(self) -> list[tuple[str, tuple[int, int]]]: ...


@dataclass
class WeChatX11Driver:
    runner: X11Runner
    _sequence: int = 0

    def send_text(self, search_key: str, text: str) -> str:
        if not search_key or not text:
            raise ValueError("search_key and text are required")
        if search_key != "@active":
            self.runner.open_search()
            self.runner.type_search(search_key)
            result_text = self.runner.capture_ocr()
            if search_key not in result_text:
                raise RuntimeError("search verification failed")
            self.runner.click_search_result(search_key)
        self.runner.paste_and_send(text)
        self._sequence += 1
        return f"wechat-outbound-{self._sequence}"

    def read_active_bubbles(self) -> list[tuple[str, tuple[int, int]]]:
        return self.runner.read_active_bubbles()

    def copy_private_bubble(self, point: tuple[int, int]) -> str | None:
        return self.runner.copy_bubble_text(point, menu_origin=(500, 480))

    def poll_text(self):
        raise NotImplementedError("OCR inbound polling is the next driver slice")
