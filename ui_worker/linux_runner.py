"""Production X11 runner for the verified WeChat desktop geometry."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from ui_worker.active_bubbles import parse_active_bubbles
from ui_worker.copy_menu import copy_action_point_from_tsv


class LinuxWeChatRunner:
    def __init__(
        self,
        display: str = ":99",
        window: tuple[int, int, int, int] = (129, 30, 1021, 740),
        workdir: Path | None = None,
    ) -> None:
        self.display = display
        self.x, self.y, self.width, self.height = window
        self.workdir = workdir or Path("/tmp/wechat-adapter")
        self.workdir.mkdir(parents=True, exist_ok=True)

    def _run(self, command: str) -> None:
        subprocess.run(["sh", "-c", command], check=True)

    def open_search(self) -> None:
        self._run(f"DISPLAY={self.display} xdotool mousemove {self.x + 155} {self.y + 44} click 1")
        time.sleep(0.2)

    def type_search(self, text: str) -> None:
        encoded = text.replace("'", "'\\''")
        self._run(f"printf '%s' '{encoded}' | xclip -selection clipboard; DISPLAY={self.display} xdotool key ctrl+a ctrl+v")
        time.sleep(0.8)

    def capture_ocr(self) -> str:
        self._run(f"DISPLAY={self.display} xwd -root -silent > {self.workdir / 'screen.xwd'}")
        subprocess.run([
            "convert", str(self.workdir / "screen.xwd"), "-crop", f"410x180+{self.x + 60}+{self.y + 60}",
            str(self.workdir / "search.png"),
        ], check=True)
        result = subprocess.run(["tesseract", str(self.workdir / "search.png"), "stdout", "-l", "chi_sim+eng"], capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def click_search_result(self, search_key: str) -> None:
        self._run(f"DISPLAY={self.display} xdotool mousemove {self.x + 155} {self.y + 110} click 1")
        time.sleep(0.7)

    def paste_and_send(self, text: str) -> None:
        encoded = text.replace("'", "'\\''")
        self._run(f"printf '%s' '{encoded}' | xclip -selection clipboard; DISPLAY={self.display} xdotool mousemove {self.x + 301} {self.y + 645} click 1; xdotool key ctrl+v")
        time.sleep(0.3)
        self._run(f"DISPLAY={self.display} xdotool mousemove {self.x + 951} {self.y + 706} click 1")

    def read_active_bubbles(self) -> list[tuple[str, tuple[int, int]]]:
        xwd = self.workdir / "active-bubbles.xwd"
        png = self.workdir / "active-bubbles.png"
        threshold = self.workdir / "active-bubbles-threshold.png"
        self._run(f"DISPLAY={self.display} xwd -root -silent > {xwd}")
        subprocess.run(["convert", str(xwd), "-crop", "700x530+430+100", "-resize", "300%", "-colorspace", "Gray", "-contrast-stretch", "1%x1%", str(png)], check=True)
        result = subprocess.run(["tesseract", str(png), "stdout", "-l", "chi_sim+eng", "--psm", "11", "tsv"], capture_output=True, text=True, check=True)
        return [(bubble.key, bubble.point) for bubble in parse_active_bubbles(result.stdout, crop_origin=(430, 100), split_x=350, scale=3)]

    def copy_bubble_text(self, point: tuple[int, int], menu_origin: tuple[int, int]) -> str | None:
        x, y = point
        menu_png = self.workdir / "copy-menu.png"
        menu_tsv = self.workdir / "copy-menu.tsv"
        self._run(f"DISPLAY={self.display} xdotool mousemove {x} {y} click 3")
        time.sleep(0.4)
        try:
            self._run(f"DISPLAY={self.display} xwd -root -silent > {self.workdir / 'copy-menu.xwd'}")
            subprocess.run([
                "convert", str(self.workdir / "copy-menu.xwd"), "-crop", "360x320+500+480",
                "-resize", "300%", "-colorspace", "Gray", "-contrast-stretch", "1%x1%", "-threshold", "70%", str(menu_png),
            ], check=True)
            result = subprocess.run(["tesseract", str(menu_png), "stdout", "-l", "chi_sim+eng", "--psm", "11", "tsv"], capture_output=True, text=True, check=True)
            menu_tsv.write_text(result.stdout)
            copy_point = copy_action_point_from_tsv(result.stdout, menu_origin, 3)
            if copy_point is None:
                return None
            self._run(f"DISPLAY={self.display} xdotool mousemove {copy_point[0]} {copy_point[1]} click 1")
            time.sleep(0.3)
            copied = subprocess.run(["sh", "-c", f"DISPLAY={self.display} xclip -o -selection clipboard"], capture_output=True, text=True, check=True)
            return copied.stdout
        finally:
            self._run(f"DISPLAY={self.display} xdotool key Escape")
