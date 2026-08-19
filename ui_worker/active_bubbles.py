"""Parse visible left-side OCR rows into conservative Copy candidates."""
from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class ActiveBubble:
    key: str
    text: str
    point: tuple[int, int]


def parse_active_bubbles(tsv: str, crop_origin: tuple[int, int], split_x: int, scale: int = 1) -> list[ActiveBubble]:
    groups: dict[tuple[str, str, str], list[dict[str, int | str]]] = {}
    for row in csv.DictReader(tsv.splitlines(), delimiter="\t"):
        text = row.get("text", "").strip()
        try:
            confidence = float(row.get("conf", "-1"))
            left, top = int(row["left"]) // scale, int(row["top"]) // scale
            width, height = int(row["width"]) // scale, int(row["height"]) // scale
        except (KeyError, ValueError):
            continue
        if not text or confidence < 40 or left < 0 or left + width >= split_x:
            continue
        key = (row.get("block_num", ""), row.get("par_num", ""), row.get("line_num", ""))
        groups.setdefault(key, []).append({"text": text, "left": left, "top": top, "width": width, "height": height})
    bubbles: list[ActiveBubble] = []
    ox, oy = crop_origin
    for words in groups.values():
        words.sort(key=lambda item: int(item["left"]))
        left = min(int(item["left"]) for item in words)
        top = min(int(item["top"]) for item in words)
        right = max(int(item["left"]) + int(item["width"]) for item in words)
        bottom = max(int(item["top"]) + int(item["height"]) for item in words)
        text = " ".join(str(item["text"]) for item in words)
        evidence = f"{left}:{top}:{right-left}:{bottom-top}:{text}"
        bubbles.append(ActiveBubble(hashlib.blake2b(evidence.encode(), digest_size=16).hexdigest(), text, (ox + (left + right) // 2, oy + (top + bottom) // 2)))
    return bubbles
