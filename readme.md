[English](./readme.md) | [中文](./readme_cn.md)
# Copilot Proxy

Convert GitHub Copilot into an OpenAI-compatible API with one click. Works with [Continue](https://continue.dev) and other plugins.


## ✨ Features

- **One-Click Auth** - Automatic GitHub OAuth device-flow on first run, no manual token copying
- **Auto Refresh** - Background automatic Copilot Token refresh, zero intervention needed
- **Remember Login** - Token saved locally, auto-restored on next launch
- **OpenAI Compatible** - Standard OpenAI API format, works with any compatible client
- **Bypass Education/Free plan restrictions on models like Claude**

## 📋 Prerequisites

1. **GitHub account** with one of the following enabled:
   - [Copilot Free](https://github.com/settings/copilot)
   - Copilot Pro
   - Copilot Education

2. **Python 3.7+**

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Script

```bash
python main.py
```

### 3. First-Time Authorization

The script will automatically open your browser. Follow the prompts:

```
[1/3] Requesting device verification code...

[2/3] Please complete authorization in your browser:

  ┌─────────────────────────────┐
  │                             │
  │     Code:  ABCD-1234        │
  │                             │
  └─────────────────────────────┘

  Open: https://github.com/login/device
  (Browser opened automatically)

[3/3] Waiting for authorization...

[✓] Authorization successful!
```

### 4. Configure Continue

Open Continue's `config.yaml` and add model configurations:

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

  # Code Completion (Tab)
  - name: Codex Mini (Copilot)
    provider: openai
    model: gpt-5.1-codex-mini
    apiBase: http://localhost:{PROXY_PORT}
    apiKey: "dummy"
    roles:
      - autocomplete
```

### 5. Start Using

Open the Continue sidebar in VS Code, select a model, and start chatting.

## 🔧 Advanced Usage

### Change Port

Edit the top of `main.py`:

```python
PROXY_PORT = 15432  # Change to your desired port
```

### Re-authorize

Delete the token file and re-run:

```bash
rm .copilot_token.json
python main.py
```

### Use as a Backend for Other Tools

Any tool that supports the OpenAI API format can connect:

```
API Base: http://localhost:15432
API Key:  any value (e.g. "dummy")
Model:    claude-sonnet-4.6
```

### Model Fallback

- **What it does**: If a requested model is unavailable for your Copilot account (the Copilot API returns a `model_not_supported` error), the proxy can automatically retry the request using a supported fallback model so clients don't fail immediately.

- **How it works**: On startup the proxy selects a fallback model by querying the Copilot models endpoint (selection logic lives in `fallback.py`). The default priority list is defined in `fallback.py` (for example: `gpt-4.1`, `gpt-4o`, `gpt-5-mini`, `raptor-mini`). When the upstream returns a 400 with code `model_not_supported`, the proxy replaces the top-level `model` field in the client JSON with the chosen fallback model and retries once. The proxy also exposes the currently selected fallback via `GET /fallback`.

- **Customize**: Edit `fallback.py` to change the `PREFERRED_PREFIXES` or the selection logic. The script will pick the first usable model matching the configured priorities.

- **Check current fallback**:

```bash
curl -sS http://localhost:15432/fallback
```

- **Testing**: point a client at `http://localhost:15432` and request an unsupported model (e.g., `claude-mythos-preview`) — watch the proxy logs for fallback messages.

## 🏗️ How It Works

```
Continue / Other Clients
        │
        │ POST /chat/completions (OpenAI format)
        ▼
┌───────────────────────┐
│  copilot_proxy.py     │  localhost:15432
│                       │
│  • OAuth device flow  │
│  • Auto token refresh │
│  • Request forwarding │
└───────────────────────┘
        │
        │ Bearer <copilot_token>
        ▼
GitHub Copilot API
        │
        ▼
Claude / GPT / Gemini
```

1. **OAuth Authorization** - Obtain a long-lived `ghu_` token via GitHub device flow
2. **Token Exchange** - Exchange the `ghu_` token for a short-lived Copilot token (~30 min validity)
3. **Auto Refresh** - Background refresh of the Copilot token every 25 minutes
4. **Request Forwarding** - Forward OpenAI-format requests to the Copilot API with valid credentials

## ❓ FAQ

### Q: Copilot Token refresh failed?

Make sure your GitHub account has Copilot enabled: https://github.com/settings/copilot

### Q: Model returns 401/403?

The token may have expired. Restart the script to auto-refresh.

### Q: Some models are unavailable?

Different Copilot subscription tiers have access to different models. The free plan may not support all models.

### Q: Can I use it on another computer?

Each computer needs to run the script and authorize separately. Do not copy `.copilot_token.json` to other machines.

### Q: Is it secure?

- Tokens are only stored locally in your `.copilot_token.json` file
- All requests communicate directly with the official GitHub API
- No third-party servers involved

## 📄 License

MIT
