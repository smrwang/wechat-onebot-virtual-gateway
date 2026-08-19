# WeChat Virtual Gateway

[简体中文](./README.md) | **English**

A Docker-first **OneBot V11 WeChat gateway** for Chinese users: runs the official WeChat Linux client inside a private X11 virtual desktop, and lets you configure forward/reverse WebSocket through a management panel.

> **Current status**: private-message outbound is verified; private-message inbound is still experimental and disabled by default; group chats and native `@` mentions are not yet supported.

## Testing & Feedback

This project has so far only been tested through:

- Manual QR-code login and manual UI verification;
- A OneBot V11 WebSocket client written in a local Shell;
- Local unit tests for Docker, Gateway, Worker and the panel.

It has **not been integrated with any third-party bot platform for compatibility testing**, because the project is still in an early public beta with limited maintainers and testers.

### Testing & Feedback Group

```text
744528507
```

You are welcome to join the group and report issues. When reporting, please try to provide:

- Project version or Git commit;
- Linux distribution and Docker version;
- Whether you use reverse WS or forward WS;
- The OneBot Action you called, or the event structure you received;
- Sanitized panel/Gateway logs.

Please do **not** send in the group: QR codes, access tokens, WeChat profiles, chat screenshots, chat history, or any account-private data.

## Capability Matrix

| Capability | Status | Notes |
|---|---|---|
| Official WeChat QR login in Docker | Verified | Uses the official Linux client. |
| Management panel | Verified | Login status, contact mappings, protocol config and sanitized logs. |
| OneBot V11 reverse WebSocket | Verified | Tested with a local Shell client. |
| OneBot V11 forward WebSocket | Implemented | Hot reload is supported; third-party compatibility is untested. |
| `get_friend_list` | Verified | Returns approved local contact mappings. |
| `send_private_msg` | Verified | Sends text through the deterministic WeChat UI flow. |
| Private text inbound | Experimental, disabled | Pending stronger identity and copy verification. |
| Group inbound | Not supported | Never emulated as private events. |
| Native group mentions `@` | Not supported | Literal text is not claimed as a native mention. |
| Media, files, voice, stickers, replies | Not supported | Current scope is text only. |

## Quick Start

### 1. Prepare the official WeChat installer

Download the Tencent WeChat Linux x86_64 `.deb` package from the official source and place it at:

```text
runtime/installers/WeChatLinux_x86_64.deb
```

The installer is not committed to the repository for copyright and security reasons. Please read [`runtime/installers/README.md`](runtime/installers/README.md).

### 2. Start Docker

```bash
docker compose up -d --build
```

### 3. Open the management panel

The management panel is the only interface you need for normal use:

1. Scan the official WeChat QR code in the panel;
2. Confirm the login on your phone;
3. Configure OneBot forward or reverse WS;
4. Configure approved contact mappings;
5. View sanitized runtime logs in the panel.

You do not need to enter VNC for normal use. VNC, Dashboard and Gateway are bound to localhost or the Docker internal network by default, and should not be exposed to the internet.

## OneBot V11 Usage

### Reverse WS

Default local address:

```text
ws://127.0.0.1:16700
```

Get approved contacts:

```json
{"action":"get_friend_list","params":{}}
```

Send a private text message:

```json
{
  "action": "send_private_msg",
  "params": {
    "user_id": 123456,
    "message": "你好 / Hello"
  }
}
```

A successful return from `send_private_msg` means the gateway has submitted the text through the verified WeChat UI; it does not mean the recipient has read it, nor does it represent a platform-level delivery receipt.

### Forward WebSocket

You can fill in a forward WS address in the panel and enable it. The configuration is saved at:

```text
runtime/gateway/protocol.json
```

Forward WS configuration supports hot reload; changes to the reverse WS listen address or port require a Gateway restart. Host ports are published only to `127.0.0.1` by default.

### Capability status

Call `get_status` to view the current explicit capability boundaries:

```json
{
  "private_text_inbound": false,
  "private_text_inbound_experimental": true,
  "group_inbound": false,
  "native_mentions": false,
  "requires_unpinned_unfolded_inbox": true
}
```

## Experimental Private Inbound

Private inbound is currently disabled by default. In the future, a message will only be emitted when all of the following conditions are met:

1. Approved private-chat session visual identity;
2. Two stable frames of the session list snapshot;
3. No pinned or folded sessions;
4. Verified selected row and chat title;
5. The chat area is not obscured by an auxiliary window;
6. A complete left-side inbound text bubble is successfully copied.

When using the experimental inbound feature, please do not pin sessions, and do not fold group chats/sessions. When unknown, duplicate-title, obscured, group-chat or `@` situations are encountered, the system will isolate them instead of incorrectly emitting OneBot events.

## Privacy & Security

- Do not commit `runtime/`, `evidence/`, panel tokens, WeChat profiles, SQLite, logs, or the official `.deb` to Git;
- Do not expose VNC, Docker API, SSH, Dashboard or OneBot ports;
- `.gitignore` is configured to prevent accidental commits of login credentials, QR codes and local evidence;
- This project does not emulate the private WeChat protocol, nor does it decrypt the local WeChat database;
- The official WeChat client remains subject to Tencent's applicable terms and license.

## Development & Testing

```bash
python3 -m unittest discover -s gateway/tests -v
python3 -m unittest discover -s ui_worker/tests -v
python3 -m unittest discover -s panel/tests -v
```

Current public-version test results:

```text
Gateway: 21 tests passed
UI Worker: 60 tests passed
Panel: 14 tests passed
```

## License

This project is released under the **Apache License 2.0**. The official WeChat client is not part of this project and remains subject to Tencent's applicable terms and license.
