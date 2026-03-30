"""
GitHub README同步器
每小时检测仓库更新，下载README和图片到本地
"""
import os
import re
import time
import yaml
import requests
import base64
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 不使用代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

# 创建session with better retry logic
session = requests.Session()
session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=0.5)))
# 显式设置不使用代理
session.trust_env = False
import hashlib
from datetime import datetime
from threading import Thread

README_DIR = os.path.join(os.path.dirname(__file__), 'readmes')
IMAGES_DIR = os.path.join(README_DIR, 'images')

# 确保目录存在
os.makedirs(IMAGES_DIR, exist_ok=True)

def load_config():
    """加载配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def get_github_token():
    """获取GitHub Token"""
    config = load_config()
    return config.get('github_token', '')

def get_repo_info(owner, repo):
    """获取仓库信息（最后commit时间）"""
    token = get_github_token()
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    
    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'name': data.get('name'),
                'description': data.get('description'),
                'updated_at': data.get('updated_at'),
                'html_url': data.get('html_url')
            }
    except Exception as e:
        print(f"Error getting repo info: {e}")
    return None

def get_readme_content(owner, repo):
    """获取README内容"""
    token = get_github_token()

    for filename in ['README.md', 'readme.md', 'README.MD', 'Readme.md', 'README.rst', 'readme.rst', 'README']:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
        headers = {}
        if token:
            headers['Authorization'] = f"Bearer {token}"

        try:
            response = session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                content_bytes = base64.b64decode(data['content'])
                # 尝试多种编码
                for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                    try:
                        content = content_bytes.decode(encoding)
                        return content, data.get('name', 'README.md')
                    except:
                        continue
                # 最后尝试忽略错误
                content = content_bytes.decode('utf-8', errors='ignore')
                return content, data.get('name', 'README.md')
        except Exception as e:
            continue
    return None, None

def download_image(url, owner, repo):
    """下载图片到本地"""
    import urllib.parse
    if not url or url.startswith('data:') or url.startswith('#'):
        return None
    
    # 保存原始URL用于hash
    original_url = url
    
    # 转换相对路径为绝对路径
    if not url.startswith('http://') and not url.startswith('https://'):
        # URL编码中文路径
        url_encoded = urllib.parse.quote(url, safe='/')
        # 尝试 main 和 master 分支（保留完整路径，如 images/xxx.png）
        for branch in ['main', 'master']:
            test_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{url_encoded}"
            try:
                response = session.get(test_url, timeout=5)
                if response.status_code == 200:
                    url = test_url
                    break
            except:
                continue
    
    # 生成唯一文件名
    url_hash = hashlib.md5(original_url.encode()).hexdigest()[:10]
    ext = os.path.splitext(original_url.split('?')[0])[-1] or '.png'
    # 清理文件名中的非法字符
    import re
    ext = re.sub(r'[^a-zA-Z0-9.]', '', ext)
    filename = f"{url_hash}{ext}"
    filepath = os.path.join(IMAGES_DIR, filename)
    
    # 如果已存在则跳过
    if os.path.exists(filepath):
        return f"readmes/images/{filename}"
    
    try:
        response = session.get(url, timeout=30)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return f"readmes/images/{filename}"
    except Exception as e:
        print(f"Error downloading image: {url} - {e}")
    
    return None

def process_readme_images(content, owner, repo):
    """处理README中的图片链接"""
    if not content:
        return content
    
    # 匹配markdown图片: ![alt](url "title") 或 ![alt](url)
    def replace_markdown_image(match):
        alt_text = match.group(1)
        # 提取URL（可能有title，去掉title部分）
        url_with_title = match.group(2)
        url = url_with_title.split(' ')[0] if ' ' in url_with_title else url_with_title
        url = url.split('"')[0] if '"' in url else url
        url = url.split("'")[0] if "'" in url else url
        local_url = download_image(url.strip(), owner, repo)
        if local_url:
            return f'![{alt_text}]({local_url})'
        return match.group(0)
    
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_markdown_image, content)
    
    # 匹配HTML图片: <img src="url" width="24%">
    def replace_html_image(match):
        # 获取完整标签，保留其他属性
        full_tag = match.group(0)
        # 提取src属性
        import re as re2
        src_match = re2.search(r'src=["\']([^"\']+)["\']', full_tag)
        if not src_match:
            return full_tag
        url = src_match.group(1)
        local_url = download_image(url, owner, repo)
        if local_url:
            # 替换src但保留其他属性
            return full_tag.replace(url, local_url)
        return full_tag
    
    # 更灵活的img匹配
    content = re.sub(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', replace_html_image, content)
    
    return content

def sync_readme(owner, repo):
    """同步单个仓库的README"""
    repo_info = get_repo_info(owner, repo)
    if not repo_info:
        print(f"无法获取仓库信息: {owner}/{repo}")
        return False
    
    # 检查本地是否有更新
    cache_file = os.path.join(README_DIR, f"{owner}_{repo}.json")
    local_updated = None
    if os.path.exists(cache_file):
        import json
        with open(cache_file, 'r', encoding='utf-8') as f:
            local_data = json.load(f)
            local_updated = local_data.get('updated_at')
    
    remote_updated = repo_info.get('updated_at')
    
    # 如果没有更新或本地没有缓存，则跳过
    if local_updated and remote_updated and local_updated >= remote_updated:
        print(f"README未更新: {owner}/{repo}")
        return True
    
    # 下载README
    content, filename = get_readme_content(owner, repo)
    if not content:
        print(f"无法获取README: {owner}/{repo}")
        return False
    
    # 处理图片
    content = process_readme_images(content, owner, repo)
    
    # 保存到本地
    import json
    import markdown
    html_content = markdown.markdown(content, extensions=['extra', 'tables', 'nl2br', 'fenced_code'])
    
    cache_data = {
        'owner': owner,
        'repo': repo,
        'name': repo_info.get('name'),
        'description': repo_info.get('description'),
        'html_url': repo_info.get('html_url'),
        'updated_at': remote_updated,
        'content': content,
        'html': html_content,
        'synced_at': datetime.now().isoformat()
    }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    print(f"README同步成功: {owner}/{repo}")
    return True

def sync_all_readmes(repos):
    """同步所有仓库的README"""
    print(f"开始同步 {len(repos)} 个仓库的README...")
    for repo in repos:
        owner = repo.get('owner', {}).get('login', 'stlin256')
        repo_name = repo.get('name')
        if repo_name:
            sync_readme(owner, repo_name)
    print("同步完成")

def get_local_readme(owner, repo):
    """从本地获取README"""
    cache_file = os.path.join(README_DIR, f"{owner}_{repo}.json")
    if os.path.exists(cache_file):
        import json
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def start_sync_scheduler(repos):
    """启动定时同步"""
    def run():
        while True:
            sync_all_readmes(repos)
            time.sleep(3600)  # 每小时执行一次
    
    thread = Thread(target=run, daemon=True)
    thread.start()
    print("README同步调度器已启动（每小时检测更新）")

if __name__ == '__main__':
    # 测试
    print("测试同步...")
    sync_readme('stlin256', 'AShare-AI-Stock-Picker')

# RSS缓存
RSS_CACHE_DIR = os.path.join(os.path.dirname(__file__), 'readmes', 'rss')
os.makedirs(RSS_CACHE_DIR, exist_ok=True)

def get_rss_cache(url):
    """从缓存获取RSS"""
    import json
    import base64
    url_hash = base64.urlsafe_b64encode(url.encode()).decode().replace('=', '')[:22]
    cache_file = os.path.join(RSS_CACHE_DIR, f"{url_hash}.json")

    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 检查是否过期（中午12点更新）
            cached_time = data.get('cached_at', '')
            return data
    return None

def save_rss_cache(url, title, html):
    """保存RSS到缓存"""
    import json
    from datetime import datetime
    import base64

    url_hash = base64.urlsafe_b64encode(url.encode()).decode().replace('=', '')[:22]
    cache_file = os.path.join(RSS_CACHE_DIR, f"{url_hash}.json")

    data = {
        'url': url,
        'title': title,
        'html': html,
        'cached_at': datetime.now().isoformat()
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def fetch_and_cache_rss(url):
    """获取并缓存RSS文章"""
    from bs4 import BeautifulSoup

    try:
        response = requests.get(url, timeout=10)
        # 强制使用UTF-8
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        
        article = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
        
        if article:
            for tag in article.find_all(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            html_content = str(article)
        else:
            body = soup.find('body')
            if body:
                for tag in body.find_all(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()
                html_content = str(body)
            else:
                html_content = response.text[:5000]
        
        title = soup.title.string if soup.title else url
        
        save_rss_cache(url, title, html_content)
        
        return {'status': 'ok', 'title': title, 'html': html_content, 'url': url}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def sync_all_rss(urls):
    """同步所有RSS源"""
    print(f"开始同步 {len(urls)} 个RSS源...")
    for feed in urls:
        url = feed.get('url', '')
        if url:
            fetch_and_cache_rss(url)
    print("RSS同步完成")
