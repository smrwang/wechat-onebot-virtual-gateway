# WeChat Virtual Gateway

[简体中文](./README.md) | **English**

A Docker-first **OneBot V11 WeChat gateway** for Chinese users: runs the official WeChat Linux client inside a private X11 virtual desktop, and lets you configure forward/reverse WebSocket through a management panel.

> **Current status**: private-message outbound is verified; the panel provides a toggleable private inbound Beta, disabled by default. The Beta is verified only for registered and calibrated private-text Copy experiments; it does not include automatic multi-chat scanning. Group chats and native `@` mentions are not supported.

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
| Private text inbound Beta | Panel-gated, disabled by default | Verified for registered, calibrated private-text Copy → isolated OneBot events. Automatic multi-chat scanning and production polling are not enabled. |
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

Private inbound Beta is disabled by default and can be enabled or disabled in the **Private Inbound Beta** area of the management panel. It is currently limited to **registered, calibrated private-text bubbles**: the system must confirm a Copy menu, copy the original text, and pass deduplication before it creates an isolated experimental event. The switch does not enable automatic multi-chat scanning, production Gateway polling, group chats, `@` mentions, files, images, voice, or link/article cards.

Before enabling the Beta, make sure that:

1. the conversation is not pinned or folded;
2. the private contact is registered;
3. the client version, window size, and message-bubble position have been calibrated;
4. only ordinary plain-text messages are being tested.

When using the experimental inbound feature, do not pin sessions or fold group chats/sessions. Unknown, duplicate-title, obscured, group-chat, or `@` cases are quarantined instead of emitted as incorrect OneBot events.

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
UI Worker: 85 tests passed
Panel: 17 tests passed
```

## License

This project is released under the **Apache License 2.0**. The official WeChat client is not part of this project and remains subject to Tencent's applicable terms and license.
