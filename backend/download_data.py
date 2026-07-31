"""
自动下载/更新数据文件（带版本检测，只下载有更新的文件）
    python download_data.py          # 检查更新，仅下载过期文件
    python download_data.py --pull   # 强制重新下载所有文件
"""

import os
import sys
import json


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
ETAG_FILE = os.path.join(DATA_DIR, '.etags.json')

DATASETS = {
    'airports.json': {
        'url': 'https://raw.githubusercontent.com/mwgg/Airports/master/airports.json',
        'desc': '机场数据库 (mwgg/Airports)',
    },
    'timezone_translations.json': {
        'url': 'https://raw.githubusercontent.com/LBYHKKDCYX/Flight-Assistant/refs/heads/main/backend/data/timezone_translations.json',
        'desc': '时区翻译表',
    },
}


def _load_etags():
    if not os.path.exists(ETAG_FILE):
        return {}
    try:
        with open(ETAG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_etag(filename, headers):
    etags = _load_etags()
    etags[filename] = {
        'etag': headers.get('ETag', ''),
        'last_modified': headers.get('Last-Modified', ''),
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ETAG_FILE, 'w') as f:
        json.dump(etags, f, indent=2)


def _check_newer(filename, url):
    """
    用 ETag / Last-Modified 检测远端文件是否有更新。
    返回 'up_to_date' | 'has_update' | 'no_cache'
    """
    try:
        import requests
    except ImportError:
        return 'no_cache'

    cached = _load_etags().get(filename)
    if not cached:
        return 'no_cache'

    headers = {}
    if cached.get('etag'):
        headers['If-None-Match'] = cached['etag']
    if cached.get('last_modified'):
        headers['If-Modified-Since'] = cached['last_modified']

    try:
        resp = requests.head(url, headers=headers, timeout=15)
        if resp.status_code == 304:
            return 'up_to_date'
    except Exception:
        pass
    return 'has_update'


def download_file(url, dest):
    """通用文件下载，带进度条。返回响应头字典"""
    try:
        import requests
    except ImportError:
        print("❌ 缺少 requests 库，请先安装：pip install requests")
        sys.exit(1)

    print(f"  ⏳ 正在下载: {url}")
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get('content-length', 0))

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    downloaded = 0
    with open(dest, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = min(int(downloaded / total * 100), 100)
                bar_half = pct // 5
                bar = '█' * bar_half + '░' * (20 - bar_half)
                print(f'\r  [{bar}] {pct}%', end='')
    if total:
        print()
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    print(f'  ✅ 已保存: {os.path.basename(dest)} ({size_mb:.1f} MB)')

    return resp.headers


def check_and_download(force=False):
    """检查并下载数据文件（默认仅下载有更新的）"""
    os.makedirs(DATA_DIR, exist_ok=True)
    results = []

    for filename, meta in DATASETS.items():
        dest = os.path.join(DATA_DIR, filename)

        # 文件不存在 → 必须下载
        if not os.path.exists(dest):
            try:
                headers = download_file(meta['url'], dest)
                _save_etag(filename, headers)
                results.append(('ok', filename))
            except Exception as e:
                print(f'  ❌ 下载 {filename} 失败: {e}')
                results.append(('failed', filename))
            continue

        # 文件存在 + 强制 pull → 重新下载
        if force:
            try:
                headers = download_file(meta['url'], dest)
                _save_etag(filename, headers)
                results.append(('ok', filename))
            except Exception as e:
                print(f'  ❌ 下载 {filename} 失败: {e}')
                results.append(('failed', filename))
            continue

        # 文件存在 + 非强制 → 检查是否有更新
        status = _check_newer(filename, meta['url'])
        if status == 'up_to_date':
            size_mb = os.path.getsize(dest) / (1024 * 1024)
            print(f'  ✅ {filename} 已是最新 ({size_mb:.1f} MB)')
            results.append(('skipped', filename))
        elif status == 'has_update':
            print(f'  🔄 {filename} 有新版本，正在更新...')
            try:
                headers = download_file(meta['url'], dest)
                _save_etag(filename, headers)
                results.append(('ok', filename))
            except Exception as e:
                print(f'  ❌ 更新 {filename} 失败: {e}')
                results.append(('failed', filename))
        else:  # no_cache
            print(f'  ✅ {filename} 已存在（无法检测更新）')
            results.append(('skipped', filename))

    return results


def ensure_data(force=False):
    """
    确保数据文件存在（供 app.py 启动时调用）。
    成功返 True，失败不阻塞启动。
    """
    try:
        print('[download_data] 检查数据文件...')
        results = check_and_download(force=force)
        failed = [name for status, name in results if status == 'failed']
        if failed:
            print(f'[download_data] ⚠️ 以下文件下载失败，功能将受限: {", ".join(failed)}')
        return len(failed) == 0
    except Exception as e:
        print(f'[download_data] 检查失败（不阻塞启动）: {e}')
        return False


if __name__ == '__main__':
    force = '--pull' in sys.argv
    print('✈️  航空助手 - 数据下载工具')
    print(f'  数据目录: {DATA_DIR}')
    if force:
        print('  模式: 强制重新下载所有文件')
    else:
        print('  模式: 仅下载有更新的文件')
    print('-' * 50)
    results = check_and_download(force=force)
    print('-' * 50)

    ok = sum(1 for s, _ in results if s == 'ok')
    skip = sum(1 for s, _ in results if s == 'skipped')
    fail = sum(1 for s, _ in results if s == 'failed')
    print(f'结果: {ok} 下载/更新, {skip} 跳过(已最新), {fail} 失败')
