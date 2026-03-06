# Claude Style Personal Homepage

现代化风格的个人主页，灵感来自 Claude AI 的设计。支持展示 GitHub 仓库、博客 RSS 订阅等功能。

## 特性

- 🎨 Claude 风格的现代化深色主题
- 🌈 **智能主题色**：自动从 GitHub 头像提取并智能调整（避免太淡或太鲜艳）
- 💾 **颜色缓存**：主题色自动缓存 24 小时，提升加载速度
- 📊 自动展示 GitHub 公开仓库（按 star 数排序）
- 📰 博客 RSS 订阅同步
- ⚙️ 完全配置文件驱动
- 📱 响应式设计

## 快速开始

### 1. 配置

复制示例配置文件：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，修改以下内容：

```yaml
# GitHub用户名
github_username: "your-github-username"

# 端口号
port: 8004

# RSS订阅
rss_feeds:
  - url: "https://your-blog.com/feed.xml"
    name: "我的博客"

# 个人简介
bio:
  name: "Your Name"
  title: "Developer"
  description: "Hello, I'm a developer."

# 社交链接
social:
  github: "your-github-username"
  email: "you@example.com"
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行

```bash
python app.py
```

打开浏览器访问 http://localhost:8004

## 智能主题色

### 工作原理

1. **自动提取**：从 GitHub 头像图片中提取主色调
2. **智能调整**：
   - 饱和度控制在 40%-80%（避免太淡或太鲜艳）
   - 亮度控制在 30%-70%（避免太暗或太亮）
3. **缓存机制**：颜色信息缓存 24 小时，避免重复提取

### 手动清除缓存

如需重新提取头像颜色，可访问：

```
http://localhost:8004/api/clear-cache
```

或删除 `.cache/theme_colors.json` 文件后重启服务。

## 项目结构

```
claude-style-homepage/
├── app.py              # 主程序
├── config.yaml         # 配置文件（不提交到 Git）
├── config.example.yaml # 配置示例
├── requirements.txt    # Python 依赖
├── .gitignore         # Git 忽略配置
├── .cache/            # 颜色缓存目录（自动生成）
├── templates/
│   └── index.html     # 主页模板
└── static/
    └── avatar.png     # 头像（可选）
```

## 配置说明

| 配置项 | 说明 |
|--------|------|
| `github_username` | GitHub 用户名，用于获取公开仓库 |
| `port` | 服务端口号，默认 8004 |
| `rss_feeds` | RSS 订阅源列表 |
| `bio.name` | 你的名字 |
| `bio.title` | 标题/职位 |
| `bio.description` | 个人简介 |
| `bio.avatar` | 头像路径（优先使用 GitHub 头像） |
| `social.*` | 社交链接 |

## API 接口

- `GET /` - 主页面
- `GET /api/repos` - 获取 GitHub 仓库列表
- `GET /api/rss` - 获取 RSS 订阅内容
- `GET /api/clear-cache` - 清除主题色缓存

## 注意事项

- `config.yaml` 已加入 `.gitignore`，不会提交到 Git 仓库
- `.cache/` 目录已加入 `.gitignore`，不会提交
- 请使用 `config.example.yaml` 作为模板创建自己的配置

## 许可证

MIT
