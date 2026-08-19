"""Small durable per-private-conversation cursor for overlap scans."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


class PrivateCursor:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.data = json.loads(path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}

    def _conversation(self, conversation_id: str) -> dict[str, object]:
        return self.data.setdefault(conversation_id, {"baseline": [], "seen": []})

    def _save(self) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, ensure_ascii=False, sort_keys=True))
        os.replace(temporary, self.path)

    def baseline(self, conversation_id: str, visible_messages: list[str]) -> int:
        state = self._conversation(conversation_id)
        state["baseline"] = list(visible_messages)
        state["initialized"] = True
        self._save()
        return len(visible_messages)

    def new_messages(self, conversation_id: str, visible_messages: list[str]) -> list[str]:
        state = self._conversation(conversation_id)
        baseline = list(state.get("baseline", []))
        if not baseline:
            return list(visible_messages)
        for start in range(len(visible_messages)):
            if visible_messages[start:] == baseline[-len(visible_messages[start:]):]:
                return []
        overlap = 0
        for size in range(min(len(baseline), len(visible_messages)), 0, -1):
            if baseline[-size:] == visible_messages[:size]:
                overlap = size
                break
        state["baseline"] = list(visible_messages)
        self._save()
        return list(visible_messages[overlap:])

    def accept(self, conversation_id: str, text: str, bubble_key: str) -> bool:
        key = hashlib.blake2b(f"{conversation_id}\0{bubble_key}\0{text}".encode(), digest_size=16).hexdigest()
        state = self._conversation(conversation_id)
        seen = set(state.setdefault("seen", []))
        if key in seen:
            return False
        seen.add(key)
        state["seen"] = list(seen)
        self._save()
        return True

    def seen(self, conversation_id: str, text: str, bubble_key: str) -> bool:
        key = hashlib.blake2b(f"{conversation_id}\0{bubble_key}\0{text}".encode(), digest_size=16).hexdigest()
        return key in set(self._conversation(conversation_id).get("seen", []))
