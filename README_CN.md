# OpenHomepage

[![Deploy to GitHub Pages](https://github.com/stlin256/OpenHomepage/actions/workflows/deploy.yml/badge.svg)](https://github.com/stlin256/OpenHomepage/actions/workflows/deploy.yml)
[![Demo](https://img.shields.io/badge/Demo-Live_Preview-success)](https://stlin256.github.io/OpenHomepage/)

[English](README.md) | [中文](README_CN.md)

现代化风格的个人主页，基于 Flask 构建，支持展示 GitHub 仓库、贡献图、RSS 订阅和智能主题色。

## 特性

- 🎨 现代化深色主题
- 🌈 **智能主题色**：自动从 GitHub 头像提取并智能调整（避免太淡或太鲜艳）
- 🖼️ **自动 Favicon**：根据 GitHub 头像自动生成 `favicon.ico` 图标
- 📦 **纯静态离线化访问**：所有前端依赖 (JS/CSS) 及图片均实现预抓取和本地化，无需担心 CDN 被墙
- 📊 GitHub 贡献图（heatmap 风格）
- 📦 自动展示 GitHub 公开仓库，支持**动态排序机制**（可配置按 Star 数量或最近更新排列）
- 📖 弹窗内支持 Markdown 渲染，更加入了 **Mermaid 图表渲染**、**SVG 平移缩放** 和 **Highlight.js 代码高亮**
- 📰 博客 RSS 订阅同步，并支持**自动缓存图片，无视防盗链**
- ⚙️ 完全配置文件驱动

## 快速开始

### 1. 配置

复制示例配置文件：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`：

```yaml
github_username: "your-github-username"
github_token: "ghp_xxxxxxxxxxxxxxxxxxxx"
port: 8004

rss_feeds:
  - url: "https://your-blog.com/feed.xml"
    name: "我的博客"

bio:
  name: "Your Name"
  title: "Developer"
  description: "Hello, I'm a developer."

social:
  github: "your-github-username"
  email: "you@example.com"

footer:
  text: "Created by Your Name"
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
- **配置 Token 后才能获取贡献图数据**（GitHub GraphQL API 需要认证）

## 环境变量（可选）

如果需要通过代理访问 GitHub：

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
python app.py
```

## 智能主题色

### 工作原理

1. **自动提取**：从 GitHub 头像图片中提取主色调
2. **自动 Favicon**：自动从头像生成并保存 `static/favicon.ico`
3. **智能调整**：
   - 饱和度控制在 40%-80%（避免太淡或太鲜艳）
   - 亮度控制在 30%-70%（避免太暗或太亮）
3. **缓存机制**：颜色信息缓存 24 小时，避免重复提取

### 手动清除缓存

如需重新提取头像颜色，可访问：

```
http://localhost:8004/api/clear-cache
```

或删除 `.cache/theme_colors.json` 文件后重启服务。

## 动画效果

界面采用流畅的非线性动画设计：

### 光效
- **用户名和头像**：页面加载和切换主题时触发扫光动画
- 使用 `cubic-bezier(0.4, 0, 0.2, 1)` 缓动曲线

### 入场动画（滚动触发）
- **统计卡片**：淡入+上移，带交错延迟
- **区块标题**：淡入+左侧滑入
- **贡献图**：淡入+上移
- **项目卡片**：缩放淡入，带交错延迟
- **RSS 项**：淡入+左侧滑入，带交错延迟
- 仅在滚动到实际可见区域时触发（页面加载时已可见的元素不会触发动画）

### 悬停交互
- **卡片**：`translateY(-6px) scale(1.02)` + 阴影增强
- **RSS 项**：`translateX(8px)` 滑动效果
- **贡献格子**：悬停快速放大 `scale(1.4)`
- 所有过渡使用 `cubic-bezier(0.4, 0, 0.2, 1)` 曲线

### 主题切换
点击任意调色板按钮即可切换主题，切换时伴有光效反馈。

## 项目结构

```
openhome/
├── app.py              # 主程序
├── config.yaml         # 配置文件（不提交到 Git）
├── config.example.yaml # 配置示例
├── requirements.txt    # Python 依赖
├── .gitignore         # Git 忽略配置
├── .cache/            # 缓存目录（自动生成）
├── readme_sync.py     # README & RSS 同步
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

## 部署到 GitHub Pages

项目包含 GitHub Actions 工作流，可自动部署到 GitHub Pages。

### 配置 Secrets

在 GitHub 仓库设置中添加以下 Secrets：

| Secret/Variable 名称 | 类型 | 说明 |
|------------|------|------|
| `GH_USERNAME` | Secret | GitHub 用户名 |
| `GH_TOKEN` | Secret | GitHub Token（需要 repo 权限） |
| `RSS_URL` | Secret | RSS 订阅地址 |
| `BIO_NAME` | Secret | 你的名字 |
| `BIO_TITLE` | Secret | 标题/职位 |
| `BIO_DESCRIPTION` | Secret | 个人简介 |
| `BIO_EMAIL` | Secret | 邮箱 |
| `FOOTER_TEXT` | Secret | 页脚文字 |
| `REPO_SORT_BY` | Variable (vars) | 设置为 `updated` 以按更新时间排序，默认为按 `stars` 排序 |

### 部署步骤

1. 在仓库 Settings -> Pages 中设置 Source 为 "Deploy from a branch"
2. 添加上述 Secrets
3. 推送代码到 main 分支，或手动触发 workflow
4. 访问 `https://yourusername.github.io/OpenHomepage/`

### 自动部署

- 推送到 main 分支时自动部署
- 每天凌晨自动更新（cron: `0 0 * * *`）

## 注意事项

- `config.yaml` 已加入 `.gitignore`，不会提交到 Git 仓库
- `.cache/` 目录已加入 `.gitignore`，不会提交
- 请使用 `config.example.yaml` 作为模板创建自己的配置
