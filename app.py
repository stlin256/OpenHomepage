import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
# 代理配置（用于访问GitHub API）- 留空则直连
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

"""
OpenHome - 个人主页
现代化风格，可配置，支持GitHub信息爬取和RSS订阅
"""
import yaml
import requests
import json
import os
import time
from flask import Flask, render_template, jsonify
from datetime import datetime
import feedparser
from io import BytesIO
from colorthief import ColorThief

# 配置静态文件夹用于README图片
READMES_DIR = os.path.join(os.path.dirname(__file__), 'readmes')
app = Flask(__name__)

# 自定义路由处理 readmes 文件夹
@app.route('/readmes/<path:filename>')
def serve_readmes(filename):
    from flask import send_from_directory
    return send_from_directory(READMES_DIR, filename)

# 缓存配置
CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'theme_colors.json')
CACHE_EXPIRE = 3600 * 24  # 缓存24小时

# GitHub数据缓存配置
GITHUB_CACHE_FILE = os.path.join(CACHE_DIR, 'github_data.json')
GITHUB_CACHE_EXPIRE = 3600  # GitHub数据1小时
GITHUB_CACHE_RETRY = 900    # 失败15分钟重试

from readme_sync import parse_rss, get_theme_colors, get_rss_cache, fetch_and_cache_rss, sync_all_readmes, sync_all_rss, get_local_readme, sync_readme

# 确保缓存目录存在
os.makedirs(CACHE_DIR, exist_ok=True)

# 加载配置
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

# 缓存管理
# 这些函数现在主要从 readme_sync 导入，但在 app.py 中保留对特定逻辑的支持
from readme_sync import (
    parse_rss, get_theme_colors, get_rss_cache, fetch_and_cache_rss, 
    sync_all_readmes, sync_all_rss, get_local_readme, sync_readme,
    atomic_write_json
)

# GitHub数据缓存配置
CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
GITHUB_CACHE_FILE = os.path.join(CACHE_DIR, 'github_data.json')
GITHUB_CACHE_EXPIRE = 3600  # GitHub数据1小时
GITHUB_CACHE_RETRY = 900    # 失败15分钟重试

# 确保缓存目录存在
os.makedirs(CACHE_DIR, exist_ok=True)

# GitHub数据缓存管理
def get_github_cache(key):
    """从缓存获取GitHub数据"""
    if not os.path.exists(GITHUB_CACHE_FILE):
        return None, None
    try:
        with open(GITHUB_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        if key in cache:
            cached = cache[key]
            return cached.get('data'), cached.get('timestamp')
    except Exception as e:
        print(f"Error reading GitHub cache: {e}")
    return None, None

def save_github_cache(key, data, error=None):
    """保存GitHub数据到缓存"""
    try:
        cache = {}
        if os.path.exists(GITHUB_CACHE_FILE):
            try:
                with open(GITHUB_CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            except:
                pass
        cache[key] = {
            'data': data,
            'error': error,
            'timestamp': time.time()
        }
        atomic_write_json(GITHUB_CACHE_FILE, cache)
    except Exception as e:
        print(f"Error saving GitHub cache: {e}")

def is_cache_valid(timestamp, retry=False):
    """检查缓存是否有效"""
    if timestamp is None:
        return False
    expire = GITHUB_CACHE_RETRY if retry else GITHUB_CACHE_EXPIRE
    return time.time() - timestamp < expire

# GitHub API 获取用户信息
def get_github_user(username):
    # 先检查缓存
    cached_data, cached_time = get_github_cache(f'user_{username}')
    if cached_data and is_cache_valid(cached_time):
        print(f"Using cached user data for {username}")
        return cached_data
    
    url = f"https://api.github.com/users/{username}"
    headers = {}
    token = os.environ.get('GITHUB_TOKEN', '')
    if token:
        headers['Authorization'] = f"Bearer {token}"
        
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            save_github_cache(f'user_{username}', data)
            return data
        else:
            if cached_data:
                print(f"Using stale cache for user {username} (Status: {response.status_code})")
                return cached_data
    except Exception as e:
        print(f"Error fetching GitHub user: {e}")
        if cached_data and is_cache_valid(cached_time, retry=True):
            print(f"Using stale cache for user {username} (retry)")
            return cached_data
    return None

# GitHub API 获取用户仓库
def get_github_repos(username):
    # 先检查缓存
    cached_data, cached_time = get_github_cache(f'repos_{username}')
    if cached_data and is_cache_valid(cached_time):
        print(f"Using cached repos for {username}")
        return cached_data
    
    headers = {}
    token = os.environ.get('GITHUB_TOKEN', '')
    if token:
        headers['Authorization'] = f"Bearer {token}"
        
    all_repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                page_repos = response.json()
                if not page_repos:
                    break
                all_repos.extend(page_repos)
                if len(page_repos) < 100:
                    break
                page += 1
            else:
                print(f"Failed to fetch repos page {page}. Status code: {response.status_code}")
                break
        except Exception as e:
            print(f"Error fetching GitHub repos page {page}: {e}")
            break
            
    if all_repos:
        # 过滤掉fork的仓库
        repos = [r for r in all_repos if not r.get('fork', False)]
        
        # 根据配置决定排序方式 (默认按 star 数量降序)
        sort_by = config.get('repo_sort_by') or 'stars'
        if sort_by.lower() == 'updated':
            repos.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        else:
            repos.sort(key=lambda x: x.get('stargazers_count', 0), reverse=True)
            
        result = repos[:12]
        save_github_cache(f'repos_{username}', result)
        return result
    
    if cached_data and is_cache_valid(cached_time, retry=True):
        print(f"Using stale cache for repos {username}")
        return cached_data
    return []

# GitHub GraphQL API 获取贡献数据
def get_github_contributions(username):
    """使用GitHub GraphQL API获取用户的贡献数据"""
    # 先检查缓存
    cached_data, cached_time = get_github_cache(f'contrib_{username}')
    if cached_data and is_cache_valid(cached_time):
        print(f"Using cached contributions for {username}")
        return cached_data
    
    url = "https://api.github.com/graphql"
    token = os.environ.get('GITHUB_TOKEN', '')
    
    query = """
    {
      user(login: "%s") {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """ % username
    
    try:
        if token:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(url, json={"query": query}, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data'].get('user'):
                    calendar = data['data']['user']['contributionsCollection']['contributionCalendar']
                    result = {
                        'total': calendar.get('totalContributions', 0),
                        'weeks': calendar.get('weeks', [])
                    }
                    save_github_cache(f'contrib_{username}', result)
                    return result
    except Exception as e:
        print(f"Error fetching GitHub contributions: {e}")
    
    if cached_data and is_cache_valid(cached_time, retry=True):
        print(f"Using stale cache for contributions {username}")
        return cached_data
    return None

# 从头像提取主题色（带智能调整和缓存）已移至 readme_sync.py

# 解析RSS订阅已移至 readme_sync.py

@app.route('/')
def index():
    github_username = config.get('github_username', '')
    github_token = config.get('github_token', '')
    if github_token:
        os.environ['GITHUB_TOKEN'] = github_token
    
    user_info = get_github_user(github_username) if github_username else None
    repos = get_github_repos(github_username) if github_username else []
    contributions = get_github_contributions(github_username) if github_username else None
    
    # 计算总star数
    total_stars = sum(r.get('stargazers_count', 0) for r in repos) if repos else 0
    
    # 提取主题色（带缓存）
    theme_colors = {'primary': '#d97706', 'secondary': '#f59e0b', 'gradient_start': '#d97706', 'gradient_end': '#dc2626', 'primary_rgb': [217, 119, 6]}
    if user_info and user_info.get('avatar_url'):
        colors = get_theme_colors(user_info['avatar_url'], github_username)
        # 统一格式以适配模板
        if isinstance(colors, list):
            # 解析 rgb(r, g, b) 格式并提取 primary_rgb
            def parse_rgb(rgb_str):
                import re
                match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb_str)
                if match:
                    return [int(match.group(i)) for i in range(1, 4)]
                return [217, 119, 6]
            primary_rgb = parse_rgb(colors[0]) if colors else [217, 119, 6]
            theme_colors = {
                'primary': colors[0],
                'secondary': colors[1] if len(colors) > 1 else colors[0],
                'tertiary': colors[2] if len(colors) > 2 else colors[0],
                'gradient_start': colors[0],
                'gradient_end': colors[1] if len(colors) > 1 else colors[0],
                'primary_rgb': primary_rgb,
                'palette': colors
            }
        else:
            theme_colors = colors
    
    # 加载配色方案
    saved_scheme = '0'
    scheme_file = os.path.join(os.path.dirname(__file__), '.cache', 'color_scheme.txt')
    if os.path.exists(scheme_file):
        try:
            with open(scheme_file, 'r') as f:
                saved_scheme = f.read().strip()
        except:
            pass
    
    # 获取RSS内容（带缓存）
    rss_cache_key = 'rss_feeds'
    cached_rss, rss_time = get_github_cache(rss_cache_key)
    if cached_rss and is_cache_valid(rss_time):
        rss_items = cached_rss
        print("Using cached RSS feeds")
    else:
        rss_items = []
        for feed in config.get('rss_feeds', []):
            items = parse_rss(feed.get('url', ''))
            for item in items:
                item['source'] = feed.get('name', '')
            rss_items.extend(items)
        if rss_items:
            save_github_cache(rss_cache_key, rss_items)
        elif cached_rss and is_cache_valid(rss_time, retry=True):
            rss_items = cached_rss
            print("Using stale RSS cache")
    
    return render_template('index.html',
                         config=config,
                         user_info=user_info,
                         repos=repos,
                         total_stars=total_stars,
                         rss_items=rss_items[:10],
                         theme_colors=theme_colors,
                         contributions=contributions,
                         saved_scheme=saved_scheme)

@app.route('/api/repos')
def api_repos():
    github_username = config.get('github_username', '')
    repos = get_github_repos(github_username) if github_username else []
    return jsonify(repos)

@app.route('/api/rss')
def api_rss():
    rss_items = []
    for feed in config.get('rss_feeds', []):
        items = parse_rss(feed.get('url', ''))
        for item in items:
            item['source'] = feed.get('name', '')
        rss_items.extend(items)
    return jsonify(rss_items)

# 清除缓存API
@app.route('/api/clear-cache')
def clear_cache():
    """清除主题色缓存"""
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        return jsonify({'status': 'ok', 'message': 'Cache cleared'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/save-scheme', methods=['POST'])
def save_scheme():
    """保存配色方案到服务器"""
    from flask import request
    try:
        scheme = request.json.get('scheme', '0')
        scheme_file = os.path.join(os.path.dirname(__file__), '.cache', 'color_scheme.txt')
        os.makedirs(os.path.dirname(scheme_file), exist_ok=True)
        
        # 原子性写入
        import tempfile
        fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(scheme_file), suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(str(scheme))
            os.replace(temp_path, scheme_file)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/readme/<owner>/<repo>')
def get_readme(owner, repo):
    """获取项目的README（从本地缓存）"""
    # 导入README同步模块
    try:
        from readme_sync import get_local_readme, sync_readme
        
        # 尝试从本地获取
        local_data = get_local_readme(owner, repo)
        
        if local_data:
            return jsonify({
                'status': 'ok',
                'name': local_data.get('name', repo),
                'html': local_data.get('html', ''),
                'url': local_data.get('html_url', f'https://github.com/{owner}/{repo}')
            })
        
        # 本地没有则同步一次
        sync_readme(owner, repo)
        local_data = get_local_readme(owner, repo)
        
        if local_data:
            return jsonify({
                'status': 'ok',
                'name': local_data.get('name', repo),
                'html': local_data.get('html', ''),
                'url': local_data.get('html_url', f'https://github.com/{owner}/{repo}')
            })
        
        return jsonify({'status': 'error', 'message': 'README not found'})
    except Exception as e:
        print(f"Error getting README: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/rss/<path:url>')
def get_rss_content(url):
    """获取RSS文章内容（从缓存）"""
    import urllib.parse
    
    # 解码URL
    url = urllib.parse.unquote(url)
    
    try:
        from readme_sync import get_rss_cache, fetch_and_cache_rss
        
        # 尝试从缓存获取
        cached = get_rss_cache(url)
        if cached:
            return jsonify({
                'status': 'ok',
                'title': cached.get('title', ''),
                'html': cached.get('html', ''),
                'url': url
            })
        
        # 缓存没有则获取并缓存
        result = fetch_and_cache_rss(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # 启动时预热缓存
    github_username = config.get('github_username', '')
    github_token = config.get('github_token', '')
    if github_token:
        os.environ['GITHUB_TOKEN'] = github_token

    def perform_full_sync():
        """执行全量同步任务"""
        if not github_username:
            return
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行全量同步...")
        try:
            # 1. 获取 GitHub 数据 (自动更新缓存)
            user_info = get_github_user(github_username)
            repos = get_github_repos(github_username)
            get_github_contributions(github_username)

            # 2. 同步 README
            if repos:
                from readme_sync import sync_all_readmes
                sync_all_readmes(repos)

            # 3. 同步 RSS
            rss_feeds = config.get('rss_feeds', [])
            if rss_feeds:
                from readme_sync import fetch_and_cache_rss
                from concurrent.futures import ThreadPoolExecutor
                
                all_rss_items = []
                for feed in rss_feeds:
                    items = parse_rss(feed.get('url', ''))
                    for item in items:
                        item['source'] = feed.get('name', '')
                    all_rss_items.extend(items)
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    for item in all_rss_items:
                        executor.submit(fetch_and_cache_rss, item['link'])
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 全量同步完成")
        except Exception as e:
            print(f"同步过程中出错: {e}")

    if github_username:
        print("🔄 初始预热缓存中...")
        perform_full_sync()

        # 启动后台定时同步线程 (每 2 小时)
        def sync_scheduler():
            while True:
                time.sleep(7200)
                perform_full_sync()
        
        import threading
        threading.Thread(target=sync_scheduler, daemon=True).start()
        print("🚀 后台同步调度器已启动（每 2 小时自动更新）")

    port = config.get('port', 8004)
    print(f"🚀 启动Claude风格个人主页: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
