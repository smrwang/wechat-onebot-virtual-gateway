# WeChat Virtual Gateway / 微信虚拟网关
**简体中文** | [English](./README.en.md)


一个面向中文用户的 Docker 优先 **OneBot V11 微信网关**：在私有 X11 虚拟桌面中运行官方微信 Linux 客户端，并通过管理面板配置正向/反向 WebSocket。



> **当前状态 /**：私聊出站已经过验证；私聊入站仍为实验性功能，默认关闭；群聊和原生 `@` 暂不支持。
>

## 测试与反馈

本项目目前只经过以下方式测试：

- 人工扫码登录与人工界面验证；
- 本机 Shell 编写的 OneBot V11 WebSocket 客户端；
- 本地 Docker、Gateway、Worker 和面板单元测试。

目前**没有接入任何第三方机器人平台进行兼容性测试**，原因是项目仍处于早期公开测试阶段，维护和测试人员有限。

### 测试与反馈群 

```text
744528507
```

欢迎加入测试群反馈问题。反馈时请尽量提供：

- 项目版本或 Git commit；
- Linux 发行版和 Docker 版本；
- 使用反向 WS 还是正向 WS；
- 调用的 OneBot Action 或收到的事件结构；
- 脱敏后的面板/Gateway 日志。

请勿在群里发送：二维码、访问 token、微信 profile、聊天截图、聊天记录或任何账号隐私数据。

## 当前能力矩阵

| 能力 / Capability | 状态 / Status | 说明 / Notes |
|---|---|---|
| Docker 中官方微信扫码登录 / Official WeChat QR login in Docker | 已验证 / Verified | 使用官方 Linux 客户端 / Uses the official Linux client. |
| 单一管理面板 / Management panel | 已验证 / Verified | 登录状态、联系人映射、协议配置、脱敏日志 / Login status, mappings, protocol config and sanitized logs. |
| OneBot V11 反向 WS / Reverse WebSocket | 已验证 / Verified | 已用本机 Shell 客户端测试 / Tested with a local Shell client. |
| OneBot V11 正向 WS / Forward WebSocket | 已实现 / Implemented | 支持配置热加载；第三方兼容性待测试 / Hot reload is implemented; third-party compatibility is untested. |
| `get_friend_list` | 已验证 / Verified | 返回已批准的本地联系人映射 / Returns approved local mappings. |
| `send_private_msg` | 已验证 / Verified | 可通过确定性微信 UI 发送文本 / Sends text through the deterministic WeChat UI flow. |
| 私聊文本入站 / Private text inbound | 实验性、默认关闭 / Experimental, disabled | 等待会话身份和正文复制链路进一步验证 / Pending stronger identity and copy verification. |
| 群聊入站 / Group inbound | 暂不支持 / Not supported | 不会伪装成私聊事件 / Never emulated as private events. |
| 原生群聊 `@` / Native group mentions | 暂不支持 / Not supported | 不会把普通文字冒充原生提及 / Literal text is not claimed as a native mention. |
| 文件、图片、语音、贴纸、回复 / Media, files, voice, stickers, replies | 暂不支持 / Not supported | 当前范围为文本 / Current scope is text only. |

## 快速开始

### 1. 准备官方微信安装包

从官方渠道下载 Tencent WeChat Linux x86_64 `.deb` 安装包，放到：


```text
runtime/installers/WeChatLinux_x86_64.deb
```

安装包出于版权和安全原因不会提交到仓库。请阅读 [`runtime/installers/README.md`](runtime/installers/README.md)。


### 2. 启动 Docker

```bash
docker compose up -d --build
```

### 3. 打开管理面板

管理面板是正常使用所需的唯一界面：


1. 在面板中扫描官方微信二维码；
2. 在手机上确认登录；
3. 配置 OneBot 正向或反向 WS；
4. 配置已批准的联系人映射；
5. 在面板查看脱敏运行日志；

正常使用不需要进入 VNC。VNC、Dashboard 和 Gateway 默认只绑定本机或 Docker 内部网络，不应公开到互联网。


## OneBot V11 使用方式 

### 反向 WS

默认本机地址：


```text
ws://127.0.0.1:16700
```

获取已批准联系人：


```json
{"action":"get_friend_list","params":{}}
```

发送私聊文本：


```json
{
  "action": "send_private_msg",
  "params": {
    "user_id": 123456,
    "message": "你好 / Hello"
  }
}
```

`send_private_msg` 返回成功表示网关已经通过已验证的微信 UI 提交文本，不代表对方已读或平台级投递回执。

### 正向 WS 

可以在面板中填写正向 WS 地址并启用。配置保存在：


```text
runtime/gateway/protocol.json
```

正向 WS 配置支持热加载；反向 WS 监听地址或端口变化需要重启 Gateway。宿主机端口默认只发布到 `127.0.0.1`。


### 能力状态 

调用 `get_status` 可以查看当前明确能力边界：


```json
{
  "private_text_inbound": false,
  "private_text_inbound_experimental": true,
  "group_inbound": false,
  "native_mentions": false,
  "requires_unpinned_unfolded_inbox": true
}
```

## 私聊入站实验功能 

私聊入站当前默认关闭。未来只有同时满足以下条件才会发布消息：


1. 已批准的私聊会话视觉身份；
2. 两帧稳定的会话列表快照；
3. 没有置顶或折叠会话；
4. 已验证选中行和聊天标题；
5. 聊天区没有被附属窗口遮挡；
6. 成功复制一条完整的左侧入站文本气泡；

使用实验入站功能时，请不要置顶会话，也不要折叠群聊/会话。遇到未知、重复标题、遮挡、群聊或 `@` 情况，系统会隔离而不是错误发布 OneBot 事件。



## 隐私与安全 

- 不要把 `runtime/`、`evidence/`、面板 token、微信 profile、SQLite、日志或官方 `.deb` 提交到 Git；
- 不要公开 VNC、Docker API、SSH、Dashboard 或 OneBot 端口；
- `.gitignore` 已配置用于防止登录资料、二维码和本地证据误提交；
- 项目不使用私有微信协议模拟，也不解密本地微信数据库；
- 官方微信客户端仍受腾讯相关条款和许可约束；

## 开发测试 

```bash
python3 -m unittest discover -s gateway/tests -v
python3 -m unittest discover -s ui_worker/tests -v
python3 -m unittest discover -s panel/tests -v
```

当前公开版测试结果：



```text
Gateway: 21 tests passed
UI Worker: 60 tests passed
Panel: 14 tests passed
```

## 开源协议 / License

本项目采用 **Apache License 2.0**。官方微信客户端不属于本项目，其使用仍受腾讯相关条款和许可约束。

This project is released under the **Apache License 2.0**. The official WeChat client is not part of this project and remains subject to Tencent's applicable terms and license.
