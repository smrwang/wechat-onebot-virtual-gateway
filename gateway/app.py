"""Canonical UI-event to OneBot V11 gateway service."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator

if TYPE_CHECKING:
    from gateway.protocol_config import ForwardWebSocket
    from ui_worker.adapter import Adapter

import websockets
from websockets.asyncio.server import Server, ServerConnection

from gateway.capabilities import onebot_capabilities
from gateway.contacts_api import friend_list
from gateway.forward_ws import ForwardWebSocketRuntime
from gateway.ui_worker_client import UiWorkerClient

LOGGER = logging.getLogger(__name__)


class GatewayService:
    def __init__(
        self,
        database_path: Path,
        self_id: int = 10000,
        forward_runtime: ForwardWebSocketRuntime | None = None,
        adapter: "Adapter | None" = None,
        worker_client: UiWorkerClient | None = None,
        contacts_path: Path | None = None,
    ) -> None:
        self.self_id = self_id
        self._forward_runtime = forward_runtime
        self._adapter = adapter
        self._worker_client = worker_client
        self._contacts_path = contacts_path
        self._clients: set[ServerConnection] = set()
        self._paused = False
        self._ui_events = 0
        self._database = sqlite3.connect(database_path)
        self._database.execute(
            """CREATE TABLE IF NOT EXISTS event_map (
                event_id TEXT PRIMARY KEY,
                message_id INTEGER UNIQUE NOT NULL,
                created_at INTEGER NOT NULL
            )"""
        )
        self._database.commit()

    async def close(self) -> None:
        if self._forward_runtime is not None:
            await self._forward_runtime.close()
        self._database.close()

    async def reload_forward_ws(self, config: "ForwardWebSocket") -> None:
        if self._forward_runtime is not None:
            await self._forward_runtime.close()
        self._forward_runtime = ForwardWebSocketRuntime(config)

    @staticmethod
    def stable_id(value: str) -> int:
        digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") & 0x7FFF_FFFF

    def _message_id(self, event_id: str) -> int | None:
        row = self._database.execute("SELECT message_id FROM event_map WHERE event_id = ?", (event_id,)).fetchone()
        if row:
            return None
        message_id = self.stable_id(event_id)
        self._database.execute(
            "INSERT INTO event_map (event_id, message_id, created_at) VALUES (?, ?, ?)",
            (event_id, message_id, int(time.time())),
        )
        self._database.commit()
        return message_id

    async def pause(self) -> None:
        self._paused = True

    async def resume(self) -> None:
        self._paused = False

    async def status(self) -> dict[str, Any]:
        return {"paused": self._paused, "ui_events": self._ui_events}

    async def accept_ui_event(self, payload: dict[str, Any]) -> bool:
        if self._paused:
            return False
        required = ("event_id", "conversation_id", "sender_id", "sender_name", "text")
        if any(not isinstance(payload.get(key), str) or not payload[key] for key in required):
            return False
        message_id = self._message_id(payload["event_id"])
        if message_id is None:
            return False
        self._ui_events += 1
        sender_key = str(payload["sender_id"])
        user_id = int(sender_key) if sender_key.isdecimal() else self.stable_id(sender_key)
        event = {
            "time": int(time.time()),
            "self_id": self.self_id,
            "post_type": "message",
            "message_type": "private",
            "sub_type": "normal",
            "message_id": message_id,
            "user_id": user_id,
            "message": [{"type": "text", "data": {"text": payload["text"]}}],
            "raw_message": payload["text"],
            "font": 0,
            "sender": {"user_id": user_id, "nickname": payload["sender_name"], "card": payload["sender_name"]},
        }
        await self.publish(event)
        return True

    async def publish(self, event: dict[str, object]) -> None:
        await self._publish(event)

    async def _publish(self, event: dict[str, object]) -> None:
        wire = json.dumps(event, ensure_ascii=False)
        stale: list[ServerConnection] = []
        for client in self._clients:
            try:
                await client.send(wire)
            except websockets.ConnectionClosed:
                stale.append(client)
        for client in stale:
            self._clients.discard(client)
        if self._forward_runtime is not None:
            await self._forward_runtime.publish(event)

    async def poll_worker_once(self) -> int:
        if self._worker_client is None:
            return 0
        published = 0
        for message in self._worker_client.poll_inbound():
            accepted = await self.accept_ui_event(
                {
                    "event_id": str(message.get("event_id", "")),
                    "conversation_id": str(message.get("conversation_id", "")),
                    "sender_id": str(message.get("conversation_id", "")),
                    "sender_name": str(message.get("sender_name", "unknown")),
                    "text": str(message.get("text", "")),
                }
            )
            published += int(accepted)
        if published:
            LOGGER.info("UI worker poll published=%d", published)
        return published

    @staticmethod
    def _message_text(message: object) -> str:
        if isinstance(message, str):
            return message
        if isinstance(message, list):
            return "".join(
                str(part.get("data", {}).get("text", ""))
                for part in message
                if isinstance(part, dict) and part.get("type") == "text"
            )
        return ""

    async def handle_action(self, action: str, params: dict[str, object]) -> dict[str, object]:
        if action == "get_status":
            return {"status": "ok", "retcode": 0, "data": {"online": not self._paused, "good": True, "capabilities": onebot_capabilities()}}
        if action == "get_friend_list":
            if self._contacts_path is None:
                return {"status": "ok", "retcode": 0, "data": []}
            return {"status": "ok", "retcode": 0, "data": friend_list(self._contacts_path)}
        if action != "send_private_msg":
            return {"status": "failed", "retcode": 1404, "data": None, "message": "unsupported action"}
        if self._worker_client is None and self._adapter is None:
            return {"status": "failed", "retcode": 1405, "data": None, "message": "UI worker unavailable"}
        user_id = params.get("user_id")
        text = self._message_text(params.get("message", ""))
        if user_id is None or not text:
            return {"status": "failed", "retcode": 1400, "data": None, "message": "user_id and text message required"}
        try:
            event_id = (
                self._worker_client.send_private(str(user_id), text)
                if self._worker_client is not None
                else self._adapter.send_private_text(str(user_id), text)  # type: ignore[union-attr]
            )
        except (RuntimeError, ValueError) as exc:
            return {"status": "failed", "retcode": 1401, "data": None, "message": str(exc)}
        message_id = self._message_id(event_id)
        return {"status": "ok", "retcode": 0, "data": {"message_id": message_id}}

    @asynccontextmanager
    async def reverse_websocket_server(self, host: str = "127.0.0.1", port: int = 6700) -> AsyncIterator[Server]:
        async def handler(client: ServerConnection) -> None:
            self._clients.add(client)
            await client.send(json.dumps({
                "time": int(time.time()), "self_id": self.self_id, "post_type": "meta_event",
                "meta_event_type": "lifecycle", "sub_type": "connect",
            }))
            try:
                async for raw in client:
                    request = json.loads(raw)
                    response = await self.handle_action(
                        str(request.get("action", "")),
                        request.get("params", {}) if isinstance(request.get("params", {}), dict) else {},
                    )
                    if "echo" in request:
                        response["echo"] = request["echo"]
                    try:
                        await client.send(json.dumps(response, ensure_ascii=False))
                    except websockets.ConnectionClosed:
                        break
            finally:
                self._clients.discard(client)

        server = await websockets.serve(handler, host, port)
        try:
            yield server
        finally:
            server.close()
            await server.wait_closed()
