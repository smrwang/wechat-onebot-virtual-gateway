"""Experimental private-text event construction from complete UI evidence."""
from __future__ import annotations

import hashlib


def build_private_event(user_id: str, text: str, bubble_key: str) -> dict[str, str] | None:
    normalized = " ".join(text.split())
    if not normalized or not bubble_key:
        return None
    event_id = hashlib.blake2b(f"{user_id}\0{bubble_key}\0{normalized}".encode(), digest_size=16).hexdigest()
    return {
        "event_id": event_id,
        "conversation_id": str(user_id),
        "sender_id": str(user_id),
        "sender_name": "private",
        "text": normalized,
    }
