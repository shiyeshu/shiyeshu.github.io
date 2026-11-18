# AI 交接说明（松鼠A的博客）

> 最后更新：2026-11-18
> 给接手的人 / AI：先读完本文件，再动仓库。大多数操作都有现成脚本，不要重新发明流程。

---

## 0. 一句话

这是一个 **Hugo + Blowfish（浅色主题）** 的静态博客，源码在 `main` 分支，构建产物在 `gh-pages` 分支，GitHub Pages 从 `gh-pages` 分支发布，线上域名 **https://www.sshuo.cc**。

---

## 1. 路径与仓库

| 项目 | 值 |
| --- | --- |
| 本机工作目录 | `D:\dsh-workspace` |
| **项目根 / 站点仓库** | `D:\dsh-workspace\blog-restore\blog` |
| Git 远端 | `https://github.com/shiyeshu/shiyeshu.github.io.git` |
| 当前分支 | `main`（源码）；`gh-pages`（构建产物）；`master`（旧 Hexo 站备份，勿删） |
| 文章目录 | `content/post/`（40 篇，外加 `_index.md`） |
| 图片目录 | `static/images/`（旧图按年份；写作器上传在 `static/images/posts/<slug>/`） |
| Hugo 可执行文件 | `D:\dsh-workspace\blog-restore\tools\hugo167\hugo.exe`（0.167.0 extended） |
| 写作器 | `tools/writer/`，启动 `writer.cmd`（端口 7311） |
| 发布脚本 | `deploy.cmd`（内部调用 `deploy.ps1`） |
| 站点配置 | `config/_default/*.toml` |
| 自定义样式 | `assets/css/custom.css` |

> 注意：历史上曾有一个独立的 `deploy/` 克隆目录，**已经合并进 `blog/`**。现在 `blog/` 本身就是 git 仓库，不要再找 `deploy/`。

---

## 2. 环境事实（Windows）

- **PowerShell 执行策略**默认禁止直接运行 `.ps1`，所以统一用 `.cmd` 包装：
  - 写作：双击 `writer.cmd`
  - 发布：双击 `deploy.cmd`（或在终端 `cmd /c deploy.cmd`）
- **Hugo 必须是 0.167.x extended**（Blowfish 主题声明的支持区间；0.168 会警告，Dart Sass 相关主题不适用）。
- **访问 GitHub 需要本地代理** `http://127.0.0.1:7890`（本机直连 github.com:443 会被重置）。
  - `deploy.ps1` 会自动检测 7890 并只给 `git push` 加代理参数，不需要改全局 git 配置。
  - `api.github.com` 可直连。
- **GitHub 凭据**存在 Git Credential Manager（GCM）。`tools/pages_build.py` 会通过 `git credential fill` 读取 token，用来触发/查询 Pages 构建，不需要手填。
- Python 3.10（含 Pillow，用于写作器图片压缩）；Playwright/Chrome 可用于截图验证（可选）。

---

## 3. 发布文章（标准流程）

### 方式 A：写作器（推荐）

```powershell
# 在仓库根目录：D:\dsh-workspace\blog-restore\blog
.\writer.cmd          # 或双击 writer.cmd；浏览器打开 http://127.0.0.1:7311/
```

1. 填标题、日期，分类默认「自动推荐」，标签会自动推荐；
2. 正文区直接 `Ctrl+V` 粘贴截图 / 拖入图片 → 自动保存并插入 Markdown；
3. `Ctrl+S` 保存到 `content/post/`；
4. 发布：`.\deploy.cmd`（构建 → 推送 gh-pages → 触发并等待 Pages 构建，约 1 分钟）。

### 方式 B：手写 Markdown

在 `content/post/` 新建 `<YYYY-MM-DD>-<slug>.md`：

```yaml
---
title: "文章标题"
date: 2026-11-18T16:00:00+08:00
lastmod: 2026-11-18T16:00:00+08:00
description: "一句话摘要，用于 SEO 与列表"
url: "/2026/11/18/<slug>/"     # 新文章也可省略，走 permalink 规则
slug: "<slug>"
author: sshuo
categories: ["网络安全"]        # 只能是 网络安全 / 开发项目 / 日常随想（或新增）
tags: ["PHP", "漏洞分析"]       # 1~4 个，尽量从既有标签里选
draft: false
---

正文……
```

然后同样运行 `.\deploy.cmd`。

### 发布脚本做了什么

1. `hugo --gc --minify` 构建 `public/`
2. 用 `git worktree` 把 `public/` 同步到 `gh-pages` 分支并提交
3. 推送 `gh-pages`（自动带代理）
4. 调 GitHub API 触发 Pages 构建并轮询，直到 `built` 或超时
5. 打印 https://www.sshuo.cc

参数：
- `deploy.cmd -DryRun`：只构建并显示与线上产物的差异，不推送
- `deploy.cmd -SkipBuild`：跳过构建，直接推送现有 `public/`

---

## 4. 站点约定

### 4.1 URL

- 老文章（迁移的 39 篇）在 front matter 用 `url:` **逐篇写死**，不要删、不要改，否则外链/评论/搜索收录会失效。
- 新文章走 `config/_default/hugo.toml` 的 `[permalinks] post = "/:year/:month/:day/:slug/"`。
- `slug` 建议用英文短横线，中文标题也可以（Hugo 会编码）。

### 4.2 分类与标签

- 分类：`网络安全`、`开发项目`、`日常随想`（目前数量 21 / 13 / 6）。
- 标签：目前 35 个唯一标签，见 `/tags/`；新文章尽量复用已有标签。
- 分类页标题在 `content/categories/_index.md`，标签页在 `content/tags/_index.md`。

### 4.3 图片

- 写作器上传：`static/images/posts/<slug>/<时间戳>-<序号>.webp`，自动压缩（WebP q82，最长边 1600px，Pillow 可选）。
- 手动放图：`static/images/` 任意子目录，Markdown 用 `/images/...` 引用。
- 已有 25 张 `img.sshuo.cc` 外链图失效（ATT&CK 一/五），其余已本地化。

---

## 5. 代码结构与常用改动

```
config/_default/
  hugo.toml         站点：域名/分页/permalink/taxonomy/outputs
  params.toml       主题参数：配色、首页、文章页、评论、搜索
  languages.zh-cn.toml  作者/头像/简介
  menus.zh-cn.toml  顶部菜单（文章/分类/标签/友链/关于）
  markup.toml       Markdown/高亮/TOC
assets/css/custom.css   正文宽度、字号、排版覆盖（顶部有 CSS 变量）
layouts/partials/comments.html   Valine 评论（LeanCloud 老应用）
layouts/partials/favicons.html   站点图标
content/post/       文章
content/page/       about-me、friends、search
themes/blowfish/    精简后的主题（不含 exampleSite）
tools/writer/       本地写作器（server.py + html/js/css + selftest.py）
tools/pages_build.py 触发/查询 Pages 构建
scripts/verify_site.py 构建后自检（全部 URL/页面/静态资源）
```

常见修改：

| 想改 | 改哪里 |
| --- | --- |
| 站点标题/域名/分页/URL 规则 | `config/_default/hugo.toml` |
| 配色、首页布局、文章页功能、评论开关 | `config/_default/params.toml` |
| 菜单 | `config/_default/menus.zh-cn.toml` |
| 正文宽度/字号/行距 | `assets/css/custom.css` 顶部变量 |
| 作者头像/简介 | `config/_default/languages.zh-cn.toml` |
| 评论区 | `layouts/partials/comments.html` |
| 写作器行为 | `tools/writer/server.py`（分类/标签规则、压缩参数） |

---

## 6. 验证清单（改完必须做）

```powershell
cd D:\dsh-workspace\blog-restore\blog
..\tools\hugo167\hugo.exe --gc --minify --cacheDir ..\.hugo-cache
python scripts\verify_site.py --site . --public public
```

- 期望：`发现文章: 40`、`PASS`
- 线上抽查（需要代理）：首页、`/categories/`、`/tags/`、最新文章 URL、文章页评论区是否加载 `valine.min.js`
- 截图：Chrome headless 或 Playwright（Playwright 已安装，可用 `proxy={"server":"http://127.0.0.1:7890"}` 访问线上）

---

## 7. 已知状态与坑

1. **部署模式是 gh-pages 分支**（2026-10-19 GitHub Actions 故障时的应急方案）。`.github/workflows/hugo.yml` 仍在，但触发条件已改为 `workflow_dispatch`，避免每次 push 产生失败运行。想切回 Actions：Pages Source 改成 GitHub Actions，并把 workflow 的 `on: push branches: [main]` 恢复。
2. **不要直接 `git push` 就以为上线**：`main` 只放源码；线上来自 `gh-pages`。必须运行 `deploy.cmd`。
3. **PowerShell 不能直接跑 .ps1**：用 `.cmd` 包装，或 `powershell -ExecutionPolicy Bypass -File ...`。
4. **git push 必须走代理** 7890（脚本自动处理；手动 push 时加 `-c http.proxy=http://127.0.0.1:7890`）。
5. `public/`、`resources/`、`.hugo_build.lock` 已在 `.gitignore`，不要提交。
6. `master` 是旧 Hexo 成品备份，不要删；回滚时可切回。
7. 25 张 `img.sshuo.cc` 图片已失效，暂无来源；其余图片本地化。
8. Blowfish 会把标签显示为首字母大写（`chatGPT` → `ChatGPT`），front matter 保留原样，不影响链接。

---

## 8. 交接给 AI 时的启动提示词（复制即用）

```text
你在 Windows 机器上接手我的静态博客项目。

项目根目录：D:\dsh-workspace\blog-restore\blog
这是 git 仓库（GitHub: shiyeshu/shiyeshu.github.io）：
- main 分支 = Hugo 源码
- gh-pages 分支 = 构建产物，GitHub Pages 从它发布
- 线上：https://www.sshuo.cc
- master 分支 = 旧 Hexo 站备份，不要动

请先完整阅读仓库里的 AI-HANDOFF.md 和 README.md，再开始工作。

环境要点：
- Hugo 0.167.0 extended 在 D:\dsh-workspace\blog-restore\tools\hugo167\hugo.exe
- PowerShell 执行策略禁止 .ps1，统一用 deploy.cmd / writer.cmd
- git push 需要代理 http://127.0.0.1:7890（deploy.ps1 会自动处理）
- 发布唯一入口：仓库根目录运行 .\deploy.cmd（构建→推 gh-pages→触发 Pages）
- 验证：python scripts\verify_site.py --site . --public public

约束：
- 不要修改 content/post 里已有文章的 url 字段
- 不要提交 public/、resources/
- 不要删除 master 分支
- 未经我确认，不要执行 git push / deploy.cmd 之外可能有副作用的操作

我的当前任务：<在这里写你要 AI 做的事>
```

---

## 9. 当前快照（2026-11-18）

| 项目 | 值 |
| --- | --- |
| 文章数 | 40 |
| 分类 | 网络安全 21 / 开发项目 13 / 日常随想 6 |
| 唯一标签 | 35 |
| main HEAD | `8639643` |
| gh-pages HEAD | `4833e1d` |
| 主题 | Blowfish，浅色，ocean 配色 |
| 评论 | Valine（LeanCloud，5 条历史评论） |
| 搜索 | Blowfish 内置 Fuse（Ctrl K） |
