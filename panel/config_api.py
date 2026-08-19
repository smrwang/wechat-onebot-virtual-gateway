"""Validated panel-side writes for contacts and OneBot protocol config."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from gateway.protocol_config import ForwardWebSocket, ProtocolConfig, ProtocolStore, ReverseWebSocket
from ui_worker.contact_map import ContactMapStore


def private_inbound_beta_enabled(path: Path) -> bool:
    try:
        return json.loads(path.read_text()).get("enabled") is True
    except (FileNotFoundError, json.JSONDecodeError):
        return False


def apply_private_inbound_beta(path: Path, payload: dict[str, Any]) -> bool:
    enabled = payload.get("enabled")
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be a boolean")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"enabled": enabled}))
    os.replace(temporary, path)
    return enabled


def apply_contact_mapping(path: Path, payload: dict[str, Any]) -> None:
    user_id = str(payload.get("user_id", ""))
    search_key = str(payload.get("search_key", ""))
    ContactMapStore(path).set(user_id, search_key)


def apply_protocol_config(path: Path, payload: dict[str, Any]) -> ProtocolConfig:
    current = ProtocolStore(path).load()
    reverse = payload.get("reverse_ws", {})
    requested_bind = str(reverse.get("bind_host", current.reverse_ws.bind_host))
    if requested_bind not in {"0.0.0.0", "127.0.0.1"}:
        raise ValueError("bind_host is restricted to local deployment values")
    # Docker publishes this service only to 127.0.0.1; 0.0.0.0 is container-internal.
    forward = payload.get("forward_ws", {})
    config = ProtocolConfig(
        reverse_ws=ReverseWebSocket(
            enabled=bool(reverse.get("enabled", current.reverse_ws.enabled)),
            bind_host=requested_bind,
            port=int(reverse.get("port", current.reverse_ws.port)),
        ),
        forward_ws=ForwardWebSocket(
            enabled=bool(forward.get("enabled", current.forward_ws.enabled)),
            url=str(forward.get("url", current.forward_ws.url)),
        ),
    )
    ProtocolStore(path).save(config)
    return config
