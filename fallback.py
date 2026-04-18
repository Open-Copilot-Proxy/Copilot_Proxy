import requests
import logging

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

def choose_fallback_model(models_url='http://127.0.0.1:15432/v1/models'):
    """
    从本地代理的 /v1/models 中选择优先的 fallback 模型。

    选择策略：
    1. 按 PREFERRED_PREFIXES 中的前缀顺序，查找第一个存在且未被 disabled 的模型（匹配 id/version/family/name）。
    2. 如果未找到，则返回第一个未被 disabled 的 model['id']。
    3. 找不到时返回 None。
    """

    try:
        r = requests.get(models_url, timeout=5)
        data = r.json()
    except Exception as e:
        logging.debug('choose_fallback_model: 请求 models 失败: %s', e)
        return None

    items = data.get('data') or []

    def matches_prefix(m, prefix):
        lower = prefix.lower()
        for key in ('id', 'version', 'name', 'family'):
            v = m.get(key)
            if not v:
                continue
            if isinstance(v, str) and v.lower().startswith(lower):
                return True
        return False

    # 按优先级查找
    for pref in PREFERRED_PREFIXES:
        for item in items:
            if matches_prefix(item, pref) and _is_enabled(item):
                return item.get('id')

    # 返回第一个 enabled 的模型
    for item in items:
        if _is_enabled(item):
            return item.get('id')

    return None

if __name__ == '__main__':
    print('Chosen fallback:', choose_fallback_model())