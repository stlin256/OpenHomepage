# OpenHomepage

[![Deploy to GitHub Pages](https://github.com/stlin256/OpenHomepage/actions/workflows/deploy.yml/badge.svg)](https://github.com/stlin256/OpenHomepage/actions/workflows/deploy.yml)
[![Demo](https://img.shields.io/badge/Demo-Live_Preview-success)](https://stlin256.github.io/OpenHomepage/)

[English](README.md) | [中文](README_CN.md)

A modern personal homepage built with Flask, featuring GitHub stats, contribution graph, RSS feed, and smart theme colors.

## Features

- 🎨 Modern dark theme
- 🌈 **Smart Theme Colors**: Auto-extracted from GitHub avatar with intelligent adjustments
- 🖼️ **Auto Favicon**: Automatically generates `favicon.ico` from your GitHub avatar
- 📦 **Fully Static & Offline-Ready**: All assets (JS/CSS) and images are pre-fetched and localized
- 📊 GitHub contribution heatmap
- 📦 GitHub repositories display with **Dynamic Sorting** (Stars or Recently Updated)
- 📖 Markdown rendering in Modals with **Mermaid Diagrams**, **SVG Pan/Zoom**, and **Highlight.js** code syntax highlighting
- 📰 Blog RSS feed subscription with **Anti-Hotlinking image caching**
- ⚙️ Fully configurable via YAML
- 🌍 Bilingual support (Chinese & English)

## Quick Start

### 1. Configure

Copy the example config:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:

```yaml
github_username: "your-github-username"
github_token: "ghp_xxxxxxxxxxxxxxxxxxxx"
port: 8004

rss_feeds:
  - url: "https://your-blog.com/feed.xml"
    name: "My Blog"

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

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python app.py
```

Visit http://localhost:8004

## GitHub Token

### Why Token?

- Without token: 60 requests/hour limit
- With token: 5000 requests/hour limit

### Generate Token

1. Login to GitHub
2. Go to Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
3. Click "Generate new token (classic)"
4. Select `repo` permission
5. Add the token to `config.yaml`

### Note

- Token is saved in `config.yaml`, which is in `.gitignore` and won't be committed
- **Token is required to fetch contribution graph data** (GitHub GraphQL API needs authentication)

## Environment Variables (Optional)

If you need proxy to access GitHub:

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
python app.py
```

## Smart Theme Colors

### How It Works

1. **Auto-extract**: Extract dominant color from GitHub avatar
2. **Auto Favicon**: Automatically generates and saves `static/favicon.ico` from your avatar
3. **Intelligent adjustment**:
   - Saturation: 40%-80% (avoid too pale or too vivid)
   - Lightness: 30%-70% (avoid too dark or too bright)
3. **Caching**: Colors cached for 24 hours

### Clear Cache Manually

Visit: http://localhost:8004/api/clear-cache

Or delete `.cache/theme_colors.json` and restart.

## Animations

The interface features smooth, nonlinear animations powered by CSS and JavaScript:

### Glow Effect
- **Username & Avatar**: Glow sweep animation on page load and theme switching
- Uses `cubic-bezier(0.4, 0, 0.2, 1)` for natural easing
- Subtle pulse effect continues after the initial sweep

### Entrance Animations
- **Stat Cards**: Fade + slide up with staggered delays (100ms, 200ms, 300ms)
- **Section Titles**: Fade + slide from left
- **Project Cards**: Scale in with staggered delays
- **RSS Items**: Fade + slide from left with staggered delays

### Hover Interactions
- **Cards**: `translateY(-6px) scale(1.02)` with enhanced shadows
- **RSS Items**: `translateX(8px)` slide effect
- **Contribution Days**: Quick `scale(1.4)` on hover
- All transitions use `cubic-bezier(0.4, 0, 0.2, 1)` for fluid motion

### Theme Switching
Click any color palette button to switch themes instantly with glow feedback.

## Project Structure

```
openhome/
├── app.py              # Main application
├── config.yaml         # Configuration (not committed)
├── config.example.yaml # Example config
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore
├── .cache/            # Cache directory
├── readme_sync.py     # README & RSS sync
├── templates/
│   └── index.html     # Main template
└── static/
    └── avatar.png     # Avatar (optional)
```

## Configuration

| Config | Description |
|--------|-------------|
| `github_username` | GitHub username |
| `github_token` | GitHub Token (optional) |
| `port` | Server port, default 8004 |
| `rss_feeds` | RSS feed list |
| `bio.name` | Your name |
| `bio.title` | Title/Position |
| `bio.description` | Bio description |
| `bio.avatar` | Avatar path |
| `social.*` | Social links |
| `footer.text` | Footer text |

## API

- `GET /` - Main page
- `GET /api/clear-cache` - Clear cache

## Deploy to GitHub Pages

The project includes GitHub Actions workflow for automatic deployment.

### Configure Secrets

Add these secrets in repository Settings -> Secrets and variables -> Actions:

| Secret/Variable | Type | Description |
|--------|------|-------------|
| `GH_USERNAME` | Secret | GitHub username |
| `GH_TOKEN` | Secret | GitHub Token with repo permission |
| `RSS_URL` | Secret | RSS feed URL |
| `BIO_NAME` | Secret | Your name |
| `BIO_TITLE` | Secret | Title/Position |
| `BIO_DESCRIPTION` | Secret | Bio description |
| `BIO_EMAIL` | Secret | Email |
| `FOOTER_TEXT` | Secret | Footer text |
| `REPO_SORT_BY` | Variable (vars) | Set to `updated` to show recent repos. Defaults to `stars` |

### Deploy Steps

1. Set Source to "Deploy from a branch" in Settings -> Pages
2. Add the secrets above
3. Push to main branch or manually trigger workflow
4. Visit `https://yourusername.github.io/OpenHomepage/`

### Auto Deploy

- Deploys automatically on push to main
- Daily auto-update at midnight (cron: `0 0 * * *`)

## Notes

- `config.yaml` is in `.gitignore`, won't be committed
- `.cache/` directory is in `.gitignore`, won't be committed
- Use `config.example.yaml` as template for your own config
