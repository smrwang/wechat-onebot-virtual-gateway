"""Local, token-gated panel for the virtual WeChat login state."""
from __future__ import annotations

import hmac
import html
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from panel.inbound_status import private_inbound_status
from panel.logs import sanitize_log_line
from panel.config_api import apply_contact_mapping, apply_private_inbound_beta, apply_protocol_config, private_inbound_beta_enabled
from panel.qr_state import login_state_from_x11
from ui_worker.contact_map import ContactMapStore

PORT = int(os.environ.get("PANEL_PORT", "9120"))
TOKEN = os.environ.get("PANEL_TOKEN", "")
RUNTIME = Path(os.environ.get("PANEL_RUNTIME", "runtime/panel"))
GATEWAY_RUNTIME = Path(os.environ.get("GATEWAY_RUNTIME", "runtime/gateway"))
PRIVATE_BETA_PATH = Path(os.environ.get("PRIVATE_BETA_PATH", "runtime/wechat-profile/adapter/private-inbound-beta.json"))


def authorized(token: str | None) -> bool:
    configured = os.environ.get("PANEL_TOKEN", "")
    return bool(configured) and isinstance(token, str) and hmac.compare_digest(configured, token)


def token_from_path(path: str) -> str | None:
    parts = [part for part in path.split("/") if part]
    return parts[0] if parts else None


def qr_image_path() -> str:
    return "qr.png"


def management_config() -> dict[str, object]:
    protocol_path = GATEWAY_RUNTIME / "protocol.json"
    contacts_path = Path("runtime/wechat-profile/adapter/contacts.json")
    protocol = json.loads(protocol_path.read_text()) if protocol_path.exists() else {}
    contacts = ContactMapStore(contacts_path)._load()
    return {"protocol": protocol, "contacts": contacts}


def runtime_logs() -> list[str]:
    try:
        output = subprocess.run(["docker", "logs", "--tail", "80", "wechat-onebot-gateway"], capture_output=True, text=True, timeout=8).stdout
    except (OSError, subprocess.SubprocessError):
        output = "Gateway log unavailable"
    allowed = ("OneBot", "Forward WebSocket", "Gateway background", "UI worker poll")
    return [sanitize_log_line(line) for line in output.splitlines() if any(marker in line for marker in allowed)][-40:]


def current_state() -> tuple[dict[str, object], Path | None]:
    raw = subprocess.check_output(
        ["docker", "exec", "wechat-virtual-desktop", "cat", "/tmp/runtime-wechat/x11-status.json"],
        text=True,
    )
    x11 = json.loads(raw)
    state = login_state_from_x11(x11)
    data: dict[str, object] = {"mode": state.mode, "qr_available": False}
    if state.window_box is None:
        return data, None
    x, y, width, height = state.window_box
    RUNTIME.mkdir(parents=True, exist_ok=True)
    xwd = RUNTIME / "login-window.xwd"
    png = RUNTIME / "login-window.png"
    subprocess.run(
        ["docker", "exec", "wechat-virtual-desktop", "sh", "-c", "DISPLAY=:99 xwd -root -silent > /tmp/panel-screen.xwd"],
        check=True,
    )
    subprocess.run(["docker", "cp", "wechat-virtual-desktop:/tmp/panel-screen.xwd", str(xwd)], check=True)
    subprocess.run(["convert", str(xwd), "-crop", f"{width}x{height}+{x}+{y}", str(png)], check=True)
    data["qr_available"] = True
    return data, png


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        token = token_from_path(parsed.path) or parse_qs(parsed.query).get("token", [None])[0]
        relative_path = "/" + "/".join([part for part in parsed.path.split("/") if part][1:])
        if not authorized(token):
            self.send_error(403, "valid panel token required")
            return
        try:
            state, image = current_state()
        except Exception as exc:
            self.send_error(503, f"panel unavailable: {exc}")
            return
        if relative_path == "/qr.png":
            if image is None:
                self.send_error(404, "login QR is not active")
                return
            body = image.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
        elif relative_path in {"/", "/index.html"}:
            status = str(state["mode"])
            config = management_config()
            protocol_json = html.escape(json.dumps(config["protocol"], ensure_ascii=False, indent=2))
            contacts_json = html.escape(json.dumps(config["contacts"], ensure_ascii=False, indent=2))
            qr = f"<img src='{qr_image_path()}' alt='WeChat login QR'>" if image else "<p>已登录，二维码不再显示。</p>"
            inbound = private_inbound_status(PRIVATE_BETA_PATH)
            beta_label = "已开启（Beta）" if inbound["beta_enabled"] else "已关闭（默认）"
            beta_action = "关闭 Beta 私聊入站" if inbound["beta_enabled"] else "开启 Beta 私聊入站"
            body = f"""<!doctype html><meta charset='utf-8'><title>WeChat Adapter Panel</title>
<style>:root{{color-scheme:light;--ink:#17212b;--muted:#5d6875;--line:#d8dee4;--surface:#fff;--canvas:#f3f5f7;--soft:#f0f3f5;--green:#07a957}}*{{box-sizing:border-box}}body{{font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--canvas);color:var(--ink);margin:0}}main{{max-width:860px;margin:28px auto;background:var(--surface);padding:26px 28px;border:1px solid var(--line)}}h1{{font-size:22px;margin:0 0 6px}}h2{{font-size:16px;margin:0 0 8px}}p{{margin:6px 0 12px}}img{{max-width:292px;width:100%;display:block;margin:18px auto}}code{{background:var(--soft);padding:2px 5px;font:13px ui-monospace,SFMono-Regular,Consolas,monospace}}pre{{background:var(--soft);padding:10px;margin:8px 0;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace}}section{{border-top:1px solid var(--line);margin-top:22px;padding-top:18px}}input,textarea{{box-sizing:border-box;width:100%;padding:10px;margin:4px 0 12px;border:1px solid #bfc7cf;border-radius:4px;background:#fff;font:14px ui-monospace,SFMono-Regular,Consolas,monospace}}button{{background:var(--green);color:#fff;border:0;padding:10px 14px;border-radius:4px;font-weight:600;min-height:40px}}button:active{{background:#078647}}small{{color:var(--muted)}}#logs{{height:260px;overflow:auto;overscroll-behavior:contain;white-space:pre;overflow-wrap:normal;background:#17212b;color:#d9e2ea;border:1px solid #0e141a;padding:12px;font:12px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace}}#result{{max-height:160px;overflow:auto}}@media(max-width:640px){{body{{background:var(--surface)}}main{{border:0;margin:0;padding:18px 16px}}h1{{font-size:20px}}section{{margin-top:18px;padding-top:16px}}button{{width:100%;margin-top:2px}}textarea{{min-height:180px}}#logs{{height:42vh;min-height:220px;max-height:360px;margin-left:-2px;margin-right:-2px;font-size:11px;padding:10px}}}}</style>
<main><h1>WeChat Adapter</h1><p>微信状态：<code>{status}</code></p>{qr}
<section><h2>联系人映射</h2><p><small>配置一次后，其他 OneBot 客户端使用对应 user_id 即可自动搜索并发送。</small></p><label>OneBot user_id</label><input id='user_id'><label>微信搜索键（昵称、备注或 wxid）</label><input id='search_key'><button onclick='saveContact()'>保存联系人映射</button><pre>{contacts_json}</pre></section>
<section><h2>私聊入站 Beta</h2><p>状态：<code>{beta_label}</code></p><p><small>仅允许已登记私聊的纯文本实验 Copy 路径；群聊、@、文件、图片、文章卡片和自动多会话扫描均不在 Beta 范围内。请勿置顶或折叠会话。</small></p><button onclick='setPrivateBeta({str(not inbound["beta_enabled"]).lower()})'>{beta_action}</button></section>
<section><h2>OneBot 协议</h2><p><small>反向 WS 与正向 WS；保存协议后重载网关生效。</small></p><textarea id='protocol' rows='12'>{protocol_json}</textarea><button onclick='saveProtocol()'>保存协议配置</button></section>
<section><h2>运行日志</h2><p><small>只显示服务状态和错误；访问令牌、聊天正文和登录资料已过滤。</small></p><button onclick='loadLogs()'>刷新日志</button><pre id='logs'>加载中…</pre></section>
<pre id='result'></pre></main>
<script>const base=location.pathname.endsWith('/')?location.pathname:location.pathname+'/';async function post(path,data){{let r=await fetch(base+path,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});document.getElementById('result').textContent=await r.text();if(r.ok)setTimeout(()=>location.reload(),500)}}async function loadLogs(){{let r=await fetch(base+'api/v1/logs');let data=await r.json();document.getElementById('logs').textContent=(data.lines||[]).join('\\n')||'暂无运行日志';}}function saveContact(){{post('api/v1/contacts',{{user_id:user_id.value,search_key:search_key.value}})}}function saveProtocol(){{try{{post('api/v1/protocol',JSON.parse(protocol.value))}}catch(e){{result.textContent=e}}}}function setPrivateBeta(enabled){{post('api/v1/private-inbound-beta',{{enabled:enabled}})}}loadLogs();</script></main>""".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif relative_path == "/api/v1/logs":
            body = json.dumps({"lines": runtime_logs()}, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif relative_path == "/api/v1/state":
            body = json.dumps({**state, **management_config(), "inbound": private_inbound_status(PRIVATE_BETA_PATH)}).encode()
        elif relative_path == "/api/v1/private-inbound-beta":
            body = json.dumps(private_inbound_status(PRIVATE_BETA_PATH)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        else:
            self.send_error(404)
            return
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        token = token_from_path(parsed.path) or parse_qs(parsed.query).get("token", [None])[0]
        relative_path = "/" + "/".join([part for part in parsed.path.split("/") if part][1:])
        if not authorized(token):
            self.send_error(403, "valid panel token required")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size))
            if relative_path == "/api/v1/contacts":
                apply_contact_mapping(Path("runtime/wechat-profile/adapter/contacts.json"), payload)
                body = json.dumps({"ok": True, "restart_required": False}).encode()
            elif relative_path == "/api/v1/private-inbound-beta":
                enabled = apply_private_inbound_beta(PRIVATE_BETA_PATH, payload)
                body = json.dumps({"ok": True, "beta_enabled": enabled, "restart_required": False}).encode()
            elif relative_path == "/api/v1/protocol":
                config = apply_protocol_config(GATEWAY_RUNTIME / "protocol.json", payload)
                body = json.dumps({"ok": True, "protocol": config.__dict__, "restart_required": True}, default=lambda o: o.__dict__).encode()
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))



def main() -> None:
    if not TOKEN:
        raise SystemExit("PANEL_TOKEN must be set")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
