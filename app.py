import os
# 代理配置（用于访问GitHub API）
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

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

app = Flask(__name__)

# 缓存配置
CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'theme_colors.json')
CACHE_EXPIRE = 3600 * 24  # 缓存24小时

# 确保缓存目录存在
os.makedirs(CACHE_DIR, exist_ok=True)

# 加载配置
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

# 缓存管理
def get_cached_colors(username):
    """从缓存获取主题色"""
    if not os.path.exists(CACHE_FILE):
        return None
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        
        if username in cache:
            cached = cache[username]
            # 检查是否过期
            if time.time() - cached.get('timestamp', 0) < CACHE_EXPIRE:
                return cached.get('colors')
    except Exception as e:
        print(f"Error reading cache: {e}")
    return None

def save_colors_to_cache(username, colors):
    """保存主题色到缓存"""
    try:
        cache = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        
        cache[username] = {
            'colors': colors,
            'timestamp': time.time()
        }
        
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"Error saving cache: {e}")

# 智能颜色调整
def adjust_color_saturation(rgb):
    """智能调整颜色饱和度，避免太淡或太鲜艳"""
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    
    # 计算亮度
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2
    
    # 计算饱和度
    if max_c == min_c:
        s = 0
    else:
        if l <= 0.5:
            s = (max_c - min_c) / (max_c + min_c)
        else:
            s = (max_c - min_c) / (2 - max_c - min_c)
    
    # 智能调整：目标饱和度在0.4-0.8之间
    target_s = max(0.4, min(0.8, s))
    
    if s == 0:
        # 无彩色，返回中灰色
        adjusted = [128, 128, 128]
    else:
        # 调整饱和度
        if s > target_s:
            # 太鲜艳，降低饱和度
            factor = target_s / s
            adjusted = [
                int(((1 - target_s) + (r - (1 - target_s)) * factor) * 255),
                int(((1 - target_s) + (g - (1 - target_s)) * factor) * 255),
                int(((1 - target_s) + (b - (1 - target_s)) * factor) * 255)
            ]
        else:
            # 太淡，提高饱和度
            factor = target_s / s if s > 0 else 1
            if l <= 0.5:
                adjusted = [
                    int((l + s * (1 - l)) * 255),
                    int((l + s * (1 - l) * g / max(r, g, b)) * 255),
                    int((l + s * (1 - l) * b / max(r, g, b)) * 255)
                ]
            else:
                adjusted = [
                    int((l + s * (1 - l) * r / max(r, g, b)) * 255),
                    int((l + s * (1 - l) * g / max(r, g, b)) * 255),
                    int((l + s * (1 - l) * b / max(r, g, b)) * 255)
                ]
    
    # 确保值在有效范围内
    adjusted = [max(0, min(255, x)) for x in adjusted]
    
    return adjusted

def adjust_color_lightness(rgb):
    """智能调整颜色亮度"""
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2  # 亮度
    
    # 目标亮度范围：0.3-0.7（避免太暗或太亮）
    target_l = max(0.3, min(0.7, l))
    
    if abs(l - target_l) > 0.1:
        # 调整亮度
        if l < target_l:
            factor = target_l / l if l > 0 else 1
        else:
            factor = target_l / l if l > 0 else 1
        
        adjusted = [int(x * factor * 255) for x in [r, g, b]]
    else:
        adjusted = list(rgb)
    
    # 确保值在有效范围内
    adjusted = [max(0, min(255, x)) for x in adjusted]
    return adjusted

def smart_adjust_color(rgb):
    """智能调整颜色（饱和度和亮度）"""
    # 先调整饱和度
    adjusted = adjust_color_saturation(rgb)
    # 再调整亮度
    adjusted = adjust_color_lightness(adjusted)
    return adjusted

# GitHub API 获取用户信息
def get_github_user(username):
    url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching GitHub user: {e}")
    return None

# GitHub API 获取用户仓库
def get_github_repos(username):
    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            repos = response.json()
            # 过滤掉fork的仓库，按star数量排序
            repos = [r for r in repos if not r.get('fork', False)]
            repos.sort(key=lambda x: x.get('stargazers_count', 0), reverse=True)
            return repos[:12]  # 返回前12个
    except Exception as e:
        print(f"Error fetching GitHub repos: {e}")
    return []

# GitHub GraphQL API 获取贡献数据
def get_github_contributions(username):
    """使用GitHub GraphQL API获取用户的贡献数据"""
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
                    return {
                        'total': calendar.get('totalContributions', 0),
                        'weeks': calendar.get('weeks', [])
                    }
    except Exception as e:
        print(f"Error fetching GitHub contributions: {e}")
    return None

# 从头像提取主题色（带智能调整和缓存）
def get_theme_colors(avatar_url, username=''):
    """从头像图片提取主题色（智能调整 + 缓存）"""
    
    # 尝试从缓存获取
    if username:
        cached = get_cached_colors(username)
        if cached:
            print(f"Using cached colors for {username}")
            return cached
    
    try:
        # 下载头像
        response = requests.get(avatar_url, timeout=10)
        if response.status_code == 200:
            img_data = BytesIO(response.content)
            color_thief = ColorThief(img_data)
            
            # 获取主色
            dominant_color = color_thief.get_color(quality=1)
            # 获取调色板
            palette = color_thief.get_palette(color_count=5, quality=1)
            
            # 转换RGB为HEX
            def rgb_to_hex(rgb):
                return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
            
            # 智能调整主色
            adjusted_primary = smart_adjust_color(dominant_color)
            adjusted_secondary = smart_adjust_color(palette[1]) if len(palette) > 1 else smart_adjust_color(palette[0])
            adjusted_tertiary = smart_adjust_color(palette[2]) if len(palette) > 2 else adjusted_secondary
            
            colors = {
                'primary': rgb_to_hex(adjusted_primary),
                'primary_rgb': adjusted_primary,
                'secondary': rgb_to_hex(adjusted_secondary),
                'tertiary': rgb_to_hex(adjusted_tertiary),
                'gradient_start': rgb_to_hex(adjusted_primary),
                'gradient_end': rgb_to_hex(adjusted_secondary)
            }
            
            # 保存到缓存
            if username:
                save_colors_to_cache(username, colors)
            
            return colors
            
    except Exception as e:
        print(f"Error extracting colors: {e}")
    
    # 默认颜色
    return {
        'primary': '#d97706',
        'secondary': '#f59e0b',
        'gradient_start': '#d97706',
        'gradient_end': '#dc2626',
        'primary_rgb': [217, 119, 6]
    }

# 解析RSS订阅
def parse_rss(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        if feed.entries:
            return [
                {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')[:200]
                }
                for entry in feed.entries[:5]
            ]
    except Exception as e:
        print(f"Error parsing RSS: {e}")
    return []

@app.route('/')
def index():
    github_username = config.get('github_username', '')
    user_info = get_github_user(github_username) if github_username else None
    repos = get_github_repos(github_username) if github_username else []
    contributions = get_github_contributions(github_username) if github_username else None
    
    # 提取主题色（带缓存）
    theme_colors = {'primary': '#d97706', 'secondary': '#f59e0b', 'gradient_start': '#d97706', 'gradient_end': '#dc2626', 'primary_rgb': [217, 119, 6]}
    if user_info and user_info.get('avatar_url'):
        theme_colors = get_theme_colors(user_info['avatar_url'], github_username)
    
    # 获取RSS内容
    rss_items = []
    for feed in config.get('rss_feeds', []):
        items = parse_rss(feed.get('url', ''))
        for item in items:
            item['source'] = feed.get('name', '')
        rss_items.extend(items)
    
    return render_template('index.html',
                         config=config,
                         user_info=user_info,
                         repos=repos,
                         rss_items=rss_items[:10],
                         theme_colors=theme_colors,
                         contributions=contributions)

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

if __name__ == '__main__':
    port = config.get('port', 8004)
    print(f"🚀 启动Claude风格个人主页: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
