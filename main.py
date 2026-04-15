#!/usr/bin/env python3
import requests
import time
import threading
import json
import os
import sys
import webbrowser
from flask import Flask, request, Response

# 配置
PROXY_PORT = 15432
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.copilot_token.json')
CLIENT_ID = 'Iv1.b507a08c87ecfe98'  # VS Code 官方 Client ID

VSCODE_HEADERS = {
    'Editor-Version': 'vscode/1.96.0',
    'Editor-Plugin-Version': 'copilot/1.246.0',
    'User-Agent': 'GithubCopilot/1.246.0',
    'Accept': 'application/json',
}

github_token = None    # ghu_ 长期 token
copilot_token = None   # 短期 copilot token

app = Flask(__name__)

# Token持久化
def save_token(token):
    """保存 GitHub token 到本地文件"""
    with open(TOKEN_FILE, 'w') as f:
        json.dump({'github_token': token}, f)
    print(f"[✓] Token 已保存到 {TOKEN_FILE}")

def load_token():
    """从本地文件加载 GitHub token"""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                return data.get('github_token')
        except:
            return None
    return None

# GitHub 设备流授权
def device_auth():
    """通过 GitHub 设备流获取 OAuth token"""
    print("\n" + "=" * 50)
    print("  GitHub Copilot 授权")
    print("=" * 50)

    # 第一步：请求设备码
    print("\n[1/3] 正在请求设备验证码...")
    r = requests.post(
        'https://github.com/login/device/code',
        headers={'Accept': 'application/json'},
        data={'client_id': CLIENT_ID, 'scope': 'read:user'}
    )
    data = r.json()

    if 'user_code' not in data:
        print(f"[✗] 请求失败: {data}")
        sys.exit(1)

    user_code = data['user_code']
    device_code = data['device_code']
    interval = data.get('interval', 5)
    expires_in = data.get('expires_in', 900)

    # 第二步：用户去浏览器授权
    print(f"\n[2/3] 请在浏览器中完成授权:")
    print(f"")
    print(f"  ┌─────────────────────────────┐")
    print(f"  │                             │")
    print(f"  │     Code:  {user_code}        │")
    print(f"  │                             │")
    print(f"  └─────────────────────────────┘")
    print(f"")
    print(f"  打开: https://github.com/login/device")
    print(f"  输入上面的验证码并授权")
    print(f"")

    # 尝试自动打开浏览器
    try:
        webbrowser.open('https://github.com/login/device')
        print("  (已自动打开浏览器)")
    except:
        print("  (请手动打开上面的链接)")

    # 第三步：轮询等待用户授权
    print(f"\n[3/3] 等待授权中... (超时: {expires_in}秒)")

    start_time = time.time()
    while time.time() - start_time < expires_in:
        time.sleep(interval)

        r = requests.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={
                'client_id': CLIENT_ID,
                'device_code': device_code,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
            }
        )
        result = r.json()

        error = result.get('error')
        if error == 'authorization_pending':
            elapsed = int(time.time() - start_time)
            print(f"  等待中... ({elapsed}秒)", end='\r')
            continue
        elif error == 'slow_down':
            interval += 5
            continue
        elif error == 'expired_token':
            print("\n[✗] 验证码已过期，请重新运行脚本")
            sys.exit(1)
        elif error == 'access_denied':
            print("\n[✗] 授权被拒绝")
            sys.exit(1)
        elif 'access_token' in result:
            token = result['access_token']
            print(f"\n\n[✓] 授权成功!")
            print(f"  Token: {token[:10]}...{token[-4:]}")
            return token
        else:
            print(f"\n[✗] 未知响应: {result}")
            sys.exit(1)

    print("\n[✗] 授权超时")
    sys.exit(1)

# Copilot Token 刷新
def refresh_copilot_token():
    """用 GitHub token 换取短期 Copilot token"""
    global copilot_token

    headers = {**VSCODE_HEADERS, 'Authorization': f'token {github_token}'}

    try:
        r = requests.get(
            'https://api.github.com/copilot_internal/v2/token',
            headers=headers
        )
        data = r.json()

        if 'token' in data:
            copilot_token = data['token']
            expires_at = data.get('expires_at', 0)
            expire_time = time.strftime('%H:%M:%S', time.localtime(expires_at))
            print(f"[✓] Copilot Token 刷新成功 (过期时间: {expire_time})")
            return True
        else:
            msg = data.get('message', str(data))
            print(f"[✗] Copilot Token 刷新失败: {msg}")
            return False
    except Exception as e:
        print(f"[✗] 请求异常: {e}")
        return False

def token_refresh_loop():
    """后台循环刷新 token"""
    while True:
        time.sleep(1500)  # 25 分钟刷新一次
        print(f"\n[~] 自动刷新 Copilot Token...")
        refresh_copilot_token()

# HTTP 代理
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    if copilot_token is None:
        return {"error": "Copilot token 未就绪，请检查授权状态"}, 503
    
    path = path[3:] if path.startswith('v1/') else path
    url = f"https://api.githubcopilot.com/{path}"

    headers = {
        'Content-Type': request.headers.get('Content-Type', 'application/json'),
        'Authorization': f'Bearer {copilot_token}',
        'Copilot-Integration-Id': 'vscode-chat',
        'Editor-Version': 'vscode/1.96.0',
        'Editor-Plugin-Version': 'copilot/1.246.0',
        'User-Agent': 'GithubCopilot/1.246.0',
        'Accept': 'application/json',
    }

    # 处理 OpenAI 兼容参数
    body = request.get_data()
    if body:
        try:
            data = json.loads(body)
            # 移除 Continue 可能发送的不兼容参数
            for key in ['api_key', 'api_base']:
                data.pop(key, None)
            body = json.dumps(data).encode()
        except:
            pass

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=body,
            stream=True,
            timeout=120
        )

        if resp.status_code != 200:
            error_text = resp.text[:500]
            print(f"[!] API 返回 {resp.status_code}: {error_text}")

        # 流式转发
        excluded_headers = ['content-encoding', 'connection']
        response_headers = {
            k: v for k, v in resp.headers.items()
            if k.lower() not in excluded_headers
        }

        return Response(
            resp.iter_content(chunk_size=1024),
            status=resp.status_code,
            headers=response_headers,
            direct_passthrough=True
        )
    except requests.exceptions.Timeout:
        return {"error": "请求超时"}, 504
    except Exception as e:
        print(f"[✗] 代理错误: {e}")
        return {"error": str(e)}, 502

@app.route('/', methods=['GET'])
def health():
    """健康检查"""
    return {
        "status": "running",
        "copilot_token_ready": copilot_token is not None,
        "proxy_port": PROXY_PORT
    }
def print_continue_config():
    print(f"\n{'=' * 50}")
    print(f"  Copilot Proxy 已启动!")
    print(f"  地址: http://localhost:{PROXY_PORT}")
    print(f"{'=' * 50}")
    print(f"按 Ctrl+C 停止代理")
    print(f"{'=' * 50}\n")

# 主入口
def main():
    global github_token

    print(r"""
   ____            _ _       _     ____
  / ___|___  _ __ (_) | ___ | |_  |  _ \ _ __ _____  ___   _
 | |   / _ \| '_ \| | |/ _ \| __| | |_) | '__/ _ \ \/ / | | |
 | |__| (_) | |_) | | | (_) | |_  |  __/| | | (_) >  <| |_| |
  \____\___/| .__/|_|_|\___/ \__| |_|   |_|  \___/_/\_\\__, |
            |_|                                         |___/
    """)

    # 1. 尝试加载已保存的 token
    github_token = load_token()

    if github_token:
        print(f"[~] 发现已保存的 Token: {github_token[:10]}...{github_token[-4:]}")
        print(f"[~] 正在验证 Token 有效性...")

        # 验证 token 是否还能用
        if refresh_copilot_token():
            print(f"[✓] Token 有效!")
        else:
            print(f"[!] Token 已失效，需要重新授权")
            github_token = None

    # 2. 如果没有有效 token，进行 OAuth 授权
    if github_token is None:
        github_token = device_auth()
        save_token(github_token)

        print(f"\n[~] 正在获取 Copilot Token...")
        if not refresh_copilot_token():
            print(f"\n[✗] 无法获取 Copilot Token")
            print(f"  可能的原因:")
            print(f"  1. 你的 GitHub 账号没有 Copilot 订阅")
            print(f"  2. 你没有 Copilot Pro / 教育版 / 免费版")
            print(f"  请确认: https://github.com/settings/copilot")

            # 删除无效 token
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            sys.exit(1)

    # 3. 启动后台 token 刷新
    t = threading.Thread(target=token_refresh_loop, daemon=True)
    t.start()

    # 4. 打印配置说明
    print_continue_config()

    # 5. 启动 Flask 代理
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)

    try:
        app.run(host='0.0.0.0', port=PROXY_PORT)
    except KeyboardInterrupt:
        print("\n\n[~] 代理已停止，下次运行会自动使用已保存的 Token")

if __name__ == '__main__':
    main()