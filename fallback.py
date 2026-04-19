import requests

PREFERRED_PREFIXES = [
    # 按优先级
    'gpt-4.1',
    'gpt-4o',
    'gpt-5-mini',
    'raptor-mini',
]

def _is_enabled(model):
    policy = model.get('policy', {}) or {}
    state = policy.get('state')
    return state != 'disabled'

def _is_picker_enabled(model):
    return model.get('model_picker_enabled', True) is not False

def _supports_endpoint(model, required_endpoint):
    endpoints = model.get('supported_endpoints')
    if not required_endpoint:
        return True
    if not endpoints:
        return True
    return required_endpoint in endpoints

def _extract_items(payload):
    # 兼容不同模型列表返回结构。
    if isinstance(payload, dict):
        if isinstance(payload.get('data'), list):
            return payload.get('data')
        if isinstance(payload.get('models'), list):
            return payload.get('models')
    if isinstance(payload, list):
        return payload
    return []

def choose_fallback_model(models_url='http://127.0.0.1:15432/v1/models', headers=None, required_endpoint='/chat/completions'):
    """
    从本地代理的 /v1/models 中选择优先的 fallback 模型

    选择策略：
    1. 按 PREFERRED_PREFIXES 中的顺序，先尝试精确 id 匹配（例如 'gpt-4.1'），若未命中再按前缀匹配 id/version/name/family
    2. 如果未找到，则返回第一个未被 disabled 的 model['id']
    3. 找不到时返回 None
    """
    
    try:
        r = requests.get(models_url, headers=headers, timeout=5)
    except Exception as e:
        print(f'[D] choose_fallback_model: 请求失败 {e}')
        return None

    if r.status_code != 200:
        preview = (r.text or '')[:120].replace('\n', ' ')
        print(f'[D] choose_fallback_model: HTTP {r.status_code}, body={preview}')
        return None

    try:
        data = r.json()
    except Exception as e:
        preview = (r.text or '')[:120].replace('\n', ' ')
        print(f'[D] choose_fallback_model: JSON 解析失败 {e}, body={preview}')
        return None

    items = _extract_items(data)
    print(f'[D] choose_fallback_model: 获取到 {len(items)} 个模型') # type: ignore

    def matches_prefix(m, prefix):
        lower = prefix.lower()
        for key in ('id', 'version', 'name', 'family'):
            v = m.get(key)
            if not v:
                continue
            if isinstance(v, str) and v.lower().startswith(lower):
                return True
        return False

    def is_usable(m):
        return _is_enabled(m) and _is_picker_enabled(m) and _supports_endpoint(m, required_endpoint)

    # 先按优先列表尝试精确 id 匹配，再按前缀匹配
    for pref in PREFERRED_PREFIXES:
        for item in items: # type: ignore
            if item.get('id') == pref and is_usable(item):
                print(f'[D] choose_fallback_model: 命中优先 id {pref}, 选择 {item.get("id")}')
                return item.get('id')
            
        for item in items: # type: ignore
            if matches_prefix(item, pref) and is_usable(item):
                print(f'[D] choose_fallback_model: 命中优先级前缀 {pref}, 选择 {item.get("id")}')
                return item.get('id')

    # 返回第一个 enabled 的模型
    for item in items: # type: ignore
        if is_usable(item):
            print(f'[D] choose_fallback_model: 无优先级匹配，返回首个 enabled: {item.get("id")}')
            return item.get('id')

    print('[D] choose_fallback_model: 没有找到任何可用模型')
    return None

if __name__ == '__main__':
    print('Chosen fallback:', choose_fallback_model())