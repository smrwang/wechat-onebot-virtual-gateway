#!/usr/bin/env python3
"""Internal deterministic UI-worker service inside the virtual desktop container."""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ui_worker.active_beta_poll import poll_active_private_beta
from ui_worker.active_private_beta import ActivePrivateBetaScanner
from ui_worker.auto_map import register_active_contact
from ui_worker.contact_map import ContactMapStore
from ui_worker.http_api import handle_experimental_private_request, handle_send_request
from ui_worker.inbound_policy import inbound_publishing_enabled
from ui_worker.private_beta import private_inbound_beta_enabled
from ui_worker.inbound import InboundDeduper, message_fingerprint
from ui_worker.ocr_reader import read_active_conversation
from ui_worker.scan_lock import scan_once_or_empty
from ui_worker.wechat_x11_driver import WeChatX11Driver
from ui_worker.linux_runner import LinuxWeChatRunner

PORT = int(os.environ.get("UI_WORKER_PORT", "9121"))
CONTACTS = ContactMapStore(Path(os.environ.get("CONTACT_MAP_PATH", "/root/.xwechat/adapter/contacts.json")))
DEDUPER = InboundDeduper(Path(os.environ.get("INBOUND_DB_PATH", "/root/.xwechat/adapter/inbound.sqlite3")))
BETA_PATH = Path(os.environ.get("PRIVATE_BETA_PATH", "/root/.xwechat/adapter/private-inbound-beta.json"))
VISUAL_REGISTRY_PATH = Path(os.environ.get("VISUAL_PRIVATE_REGISTRY_PATH", "/root/.xwechat/adapter/private-rows.json"))
ACTIVE_BETA_CURSOR_PATH = Path(os.environ.get("ACTIVE_BETA_CURSOR_PATH", "/root/.xwechat/adapter/active-private-cursor.json"))
DRIVER = WeChatX11Driver(LinuxWeChatRunner())
ACTIVE_BETA_SCANNER = ActivePrivateBetaScanner(ACTIVE_BETA_CURSOR_PATH, DRIVER)
SCAN_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/v1/poll-inbound":
            self.send_error(404)
            return
        def scan_messages() -> list[dict[str, str]]:
            messages = poll_active_private_beta(
                private_inbound_beta_enabled(BETA_PATH),
                json.loads(VISUAL_REGISTRY_PATH.read_text()) if VISUAL_REGISTRY_PATH.exists() else {},
                ACTIVE_BETA_SCANNER,
            )
            # Legacy @active + OCR publishing remains opt-in and disabled by default.
            if not messages and inbound_publishing_enabled():
                active_id = str(register_active_contact(CONTACTS))
                for text in read_active_conversation():
                    key = message_fingerprint(active_id, text)
                    if DEDUPER.accept(key):
                        messages.append({"event_id": key, "conversation_id": active_id, "sender_name": "active", "text": text})
            return messages

        try:
            messages = scan_once_or_empty(SCAN_LOCK, scan_messages)
        except Exception as exc:
            raw = json.dumps({"messages": [], "error": "worker poll failed", "detail": type(exc).__name__}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        raw = json.dumps({"messages": messages}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/v1/send-private", "/v1/experimental-private"}:
            self.send_error(404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(size))
            if self.path == "/v1/experimental-private":
                status, body = handle_experimental_private_request(payload, DRIVER, BETA_PATH)
            else:
                status, body = handle_send_request(payload, DRIVER, CONTACTS)
        except json.JSONDecodeError:
            status, body = 400, {"error": "invalid JSON"}
        except Exception as exc:
            status, body = 500, {"error": "worker operation failed", "detail": type(exc).__name__}
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
