# OpenHomepage

现代化风格的个人主页，支持展示 GitHub 仓库、贡献图、博客 RSS 订阅等功能。

![Screenshot](https://raw.githubusercontent.com/none-ai/openhome/main/screenshot.jpg)

## 特性

- 🎨 现代化深色主题
- 🌈 **智能主题色**：自动从 GitHub 头像提取并智能调整（避免太淡或太鲜艳）
- 💾 **颜色缓存**：主题色自动缓存 24 小时，提升加载速度
- 📊 GitHub 贡献图（heatmap 风格）
- 📦 自动展示 GitHub 公开仓库（按 star 数排序）
- 📰 博客 RSS 订阅同步
- ⚙️ 完全配置文件驱动
- 📱 响应式设计
- 🌍 中文字体支持

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

# GitHub Token（可选，用于提高API调用限制）
github_token: "ghp_xxxxxxxxxxxxxxxxxxxx"

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

## GitHub Token 配置

### 为什么需要 Token？

- 无 Token：每小时 60 次请求限制
- 有 Token：每小时 5000 次请求限制

### 如何生成 Token？

1. 登录 GitHub
2. 进入 Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
3. 点击 "Generate new token (classic)"
4. 勾选 `repo` 权限
5. 生成后将 Token 添加到 `config.yaml`

### 注意

- Token 会保存在 `config.yaml` 中，该文件已加入 `.gitignore`，不会提交到 Git
- 如果不配置 Token，GitHub API 会有每小时 60 次请求限制
- **配置 Token 后才能获取贡献图数据**（GitHub GraphQL API 需要认证）

## 环境变量（可选）

如果需要通过代理访问 GitHub：

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
python app.py
```

## 部署到 GitHub Pages

项目包含 GitHub Actions 工作流，可自动部署到 GitHub Pages。

### 配置 Secrets

在 GitHub 仓库设置中添加以下 Secrets：

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `GITHUB_USERNAME` | GitHub 用户名 | `stlin256` |
| `GITHUB_TOKEN` | GitHub Token（需要 repo 权限） | `ghp_xxx` |
| `RSS_URL` | RSS 订阅地址 | `https://your-blog.com/feed` |
| `BIO_NAME` | 你的名字 | `Your Name` |
| `BIO_TITLE` | 标题/职位 | `Developer` |
| `BIO_DESCRIPTION` | 个人简介 | `A passionate developer` |
| `BIO_EMAIL` | 邮箱 | `your@email.com` |
| `FOOTER_TEXT` | 页脚文字 | `Created by Your Name` |

### 部署步骤

1. 在仓库 Settings -> Pages 中设置 Source 为 "Deploy from a branch"
2. 添加上述 Secrets
3. 推送代码到 main 分支，或手动触发 workflow
4. 访问 `https://yourusername.github.io/OpenHomepage/`

### 自动部署

- 推送到 main 分支时自动部署
- 每天凌晨自动更新（cron: `0 0 * * *`）

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
openhome/
├── app.py              # 主程序
├── config.yaml         # 配置文件（不提交到 Git）
├── config.example.yaml # 配置示例
├── requirements.txt    # Python 依赖
├── .gitignore         # Git 忽略配置
├── .cache/            # 缓存目录（自动生成）
├── templates/
│   └── index.html     # 主页模板
└── static/
    └── avatar.png     # 头像（可选）
```

## 配置说明

| 配置项 | 说明 |
|--------|------|
| `github_username` | GitHub 用户名，用于获取公开仓库 |
| `github_token` | GitHub Token（可选），提高 API 限制 |
| `port` | 服务端口号，默认 8004 |
| `rss_feeds` | RSS 订阅源列表 |
| `bio.name` | 你的名字 |
| `bio.title` | 标题/职位 |
| `bio.description` | 个人简介 |
| `bio.avatar` | 头像路径（优先使用 GitHub 头像） |
| `social.*` | 社交链接 |
| `footer.text` | 页脚文字 |

## API 接口

- `GET /` - 主页面
- `GET /api/clear-cache` - 清除缓存

## 注意事项

- `config.yaml` 已加入 `.gitignore`，不会提交到 Git 仓库
- `.cache/` 目录已加入 `.gitignore`，不会提交
- 请使用 `config.example.yaml` 作为模板创建自己的配置
