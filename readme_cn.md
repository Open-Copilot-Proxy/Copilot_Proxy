[English](./readme.md) | [中文](./readme_cn.md)
# Copilot Proxy

一键将 GitHub Copilot 转为 OpenAI 兼容 API，配合 [Continue](https://continue.dev) 等插件使用。


## ✨ 特性

- **一键授权** - 首次运行自动引导 GitHub OAuth 授权，无需手动复制 token
- **自动刷新** - 后台自动刷新 Copilot Token，无需任何干预
- **记住登录** - Token 保存在本地，下次启动自动恢复
- **OpenAI兼容** - 标准 OpenAI API 格式，支持任何兼容的客户端
- **绕过Education版本对Claude等模型的限制**

## 📋 前提条件

1. **GitHub 账号**，且已开通以下任一：
   - [Copilot Free](https://github.com/settings/copilot) （免费版）
   - Copilot Pro
   - Copilot 教育版

2. **Python 3.7+**

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install flask requests
```

### 2. 运行脚本

```bash
python copilot_proxy.py
```

### 3. 首次授权

脚本会自动打开浏览器，按提示操作：

```
[1/3] 正在请求设备验证码...

[2/3] 请在浏览器中完成授权:

  ┌─────────────────────────────┐
  │                             │
  │   验证码:  ABCD-1234        │
  │                             │
  └─────────────────────────────┘

  打开: https://github.com/login/device
  (已自动打开浏览器)

[3/3] 等待授权中...

[✓] 授权成功!
```

### 4. 配置 Continue

打开 Continue 的 `config.yaml`，添加模型配置：

```yaml
models:
    # Claude Sonnet
  - name: Claude Sonnet 4.6 (Copilot_proxy)
    provider: openai
    model: claude-sonnet-4.6
    apiBase: http://localhost:{PROXY_PORT}
    apiKey: "dummy"
    roles:
      - chat
      - edit

  # Claude Opus
  - name: Claude Opus 4.6 (Copilot_proxy)
    provider: openai
    model: claude-opus-4.6
    apiBase: http://localhost:{PROXY_PORT}
    apiKey: "dummy"
    roles:
      - chat

  # GPT-5.4
  - name: GPT-5.4 (Copilot_proxy)
    provider: openai
    model: gpt-5.4
    apiBase: http://localhost:{PROXY_PORT}
    apiKey: "dummy"
    roles:
      - chat

  # Gemini 3.1 Pro preview
  - name: Gemini 3.1 Pro Preview (Copilot_proxy)
    provider: openai
    model: gemini-3.1-pro-preview
    apiBase: http://localhost:{PROXY_PORT}
    apiKey: "dummy"
    roles:
      - chat

  # 代码补全 (Tab)
  - name: Codex Mini (Copilot)
    provider: openai
    model: gpt-5.1-codex-mini
    apiBase: http://localhost:{PROXY_PORT}
    apiKey: "dummy"
    roles:
      - autocomplete
```

### 5. 开始使用

在 VS Code 中打开 Continue 侧边栏，选择模型，开始对话

## 🔧 高级用法

### 修改端口

编辑 `copilot_proxy.py` 顶部：

```python
PROXY_PORT = 15432  # 改成你想要的端口
```

### 重新授权

删除 token 文件后重新运行：

```bash
rm .copilot_token.json
python copilot_proxy.py
```

### 作为其他工具的后端

任何支持 OpenAI API 格式的工具都可以使用：

```
API Base: http://localhost:15432
API Key:  任意值（如 "dummy"）
Model:    claude-sonnet-4.6
```

## 🏗️ 工作原理

```
Continue / 其他客户端
        │
        │ POST /chat/completions (OpenAI 格式)
        ▼
┌─────────────────────┐
│  copilot_proxy.py   │  localhost:15432
│                     │
│  • OAuth 设备流授权  │
│  • 自动刷新 Token   │
│  • 请求转发         │
└─────────────────────┘
        │
        │ Bearer <copilot_token>
        ▼
GitHub Copilot API
        │
        ▼
Claude / GPT / Gemini
```

1. **OAuth 授权** - 通过 GitHub 设备流获取 `ghu_` 长期 token
2. **Token 交换** - 用 `ghu_` token 向 GitHub 换取短期 Copilot token（~30分钟有效）
3. **自动刷新** - 后台每 25 分钟自动刷新 Copilot token
4. **请求转发** - 将 OpenAI 格式请求转发到 Copilot API，附带有效的认证信息

## ❓ 常见问题

### Q: Copilot Token 刷新失败？

确认你的 GitHub 账号已开通 Copilot：https://github.com/settings/copilot

### Q: 模型返回 401/403？

可能是 token 过期了，重启脚本即可自动刷新。

### Q: 某些模型不可用？

不同的 Copilot 订阅等级可用的模型不同，免费版可能无法使用所有模型。

### Q: 能在其他电脑上用吗？

每台电脑需要单独运行脚本并授权。不要复制 `.copilot_token.json` 到其他电脑。

### Q: 安全吗？

- Token 仅保存在你本地的 `.copilot_token.json` 文件中
- 所有请求直接与 GitHub 官方 API 通信
- 不经过任何第三方服务器

## 📄 License

MIT