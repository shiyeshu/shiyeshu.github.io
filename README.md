# 松鼠A的博客

基于 [Hugo](https://gohugo.io) + [Blowfish 主题](https://github.com/nunocoracao/blowfish)（浅色方案）的静态博客，部署在 GitHub Pages，绑定域名 **https://www.sshuo.cc**。

---

## 一、写一篇新文章（日常流程）

```bash
# 1. 新建文章（文件名就是将来 URL 的一部分，建议用中文标题或英文 slug）
hugo new post/我的新文章.md

# 2. 编辑 content/post/我的新文章.md，写好正文
#    开头的 front matter 示例：
#    ---
#    title: "我的新文章"
#    date: 2026-10-20T10:00:00+08:00
#    draft: true          # 写的时候保持 true，发布前改成 false
#    description: "一句话摘要"
#    tags: ["渗透测试"]
#    categories: ["笔记"]
#    ---

# 3. 本地实时预览（Ctrl+C 退出）
hugo server -D

# 4. 浏览器打开 http://localhost:1313 看效果

# 5. 发布：把 draft 改成 false，然后提交
git add -A
git commit -m "post: 我的新文章"
git push
```

推送后 GitHub Actions 会自动构建并发布，约 1~2 分钟后线上可见（仓库 **Actions** 页可看进度）。

> 不想敲命令：也可以在 GitHub 网页上进 `content/post/` → **Add file → Create new file**，粘贴带 front matter 的 Markdown 后提交（`draft` 记得写 `false`）。

---

## 二、本地环境准备（换电脑时看）

只需装一个 Hugo 可执行文件，不需要 Node.js / npm / Ruby。

1. 下载 **Hugo extended 0.167.0**（Blowfish 主题声明支持的版本）：
   <https://github.com/gohugoio/hugo/releases/tag/v0.167.0>
   文件名形如 `hugo_extended_0.167.0_windows-amd64.zip`
2. 解压得到 `hugo.exe`，放到 PATH 里的目录；或直接在该目录运行
3. 验证：`hugo version`（应显示 `...extended...`）
4. 克隆本站：`git clone https://github.com/shiyeshu/shiyeshu.github.io`
5. 进入目录运行 `hugo server -D`

> 主题已内置在 `themes/blowfish`，**不需要** `git submodule`，克隆即用、离线也能构建。

---

## 三、目录结构

```
.
├── config/_default/          # ★ 站点配置（Blowfish 采用多文件配置）
│   ├── hugo.toml             #   标题、域名、分页、URL 规则、taxonomy
│   ├── params.toml           #   主题参数：浅色模式、首页布局、文章页、Valine 评论
│   ├── languages.zh-cn.toml  #   作者信息、头像、简介
│   ├── menus.zh-cn.toml      #   顶部/底部菜单
│   └── markup.toml           #   Markdown / 代码高亮 / TOC 设置
├── content/
│   ├── post/                 # ★ 所有文章（Markdown），_index.md 负责 /archives/ 跳转
│   └── page/                 # 独立页面：关于、友链、搜索
├── static/
│   ├── images/               # 站点图片（旧站图片按年份在此）
│   ├── js/valine.min.js      # 评论组件（本地化，不依赖 CDN）
│   ├── img/favicon.ico       # 站点图标
│   └── CNAME                 # 自定义域名，内容为 www.sshuo.cc
├── themes/blowfish/          # Blowfish 主题（已精简，不含 exampleSite）
├── layouts/
│   ├── partials/comments.html    # Valine 评论区（自定义）
│   └── partials/favicons.html    # 站点图标
├── assets/
│   └── css/custom.css        # 少量自定义样式（头像浅色描边）
├── scripts/verify_site.py    # 构建后自检：39 篇旧文 URL 是否都在
├── archetypes/post.md        # `hugo new post/xxx.md` 的模板
└── .github/workflows/hugo.yml # 自动构建 + 发布到 GitHub Pages
```

---

## 四、部署（GitHub Pages）

**站点已上线：<https://www.sshuo.cc>**（2026-10-20）

### 当前模式：gh-pages 分支 + 发布脚本

2026-10-19 晚 GitHub Actions 出现平台故障（Actions/Pages 均为 degraded），构建任务长时间排队，
因此 Pages 暂时切换为 **`gh-pages` 分支**部署：`gh-pages` 分支里放构建好的静态文件，
`main` 分支放源码。Pages 设置：**Source = Deploy from a branch / `gh-pages` / (root)**，
Custom domain = `www.sshuo.cc`。

**日常发布（当前模式）**：

```powershell
# 1. 写文章（见第一节）
# 2. 构建并发布
.\deploy.ps1
```

`deploy.ps1` 会：用 Hugo 构建 `public/` → 通过 git worktree 把产物提交到 `gh-pages` 分支 → 推送。
约 1~2 分钟后线上更新（可在仓库 Deployments 或 Pages 设置页看构建状态）。

> 如果本机访问 GitHub 需要代理（本机实测 `127.0.0.1:7890` 可用）：
> ```powershell
> git config --global http.proxy http://127.0.0.1:7890
> ```
> 发布完成后可 `git config --global --unset http.proxy` 取消。

### 切回 GitHub Actions 自动部署（Actions 恢复后，推荐）

1. 仓库 **Settings → Pages → Source** 改为 **GitHub Actions**
2. 把 `.github/workflows/hugo.yml` 里的 `on:` 恢复成：
   ```yaml
   on:
     push:
       branches: [main]
     workflow_dispatch:
   ```
3. 之后 `git push` 即自动构建发布，不再需要 `deploy.ps1`

### 首次切换时做过的事（留档）

1. 旧站备份：`master` 分支保留旧的 Hexo 成品，未删任何历史提交。
2. 源码推到 **`main`** 分支；`gh-pages` 分支放构建产物。
3. 仓库 **Settings → Pages**：Custom domain = `www.sshuo.cc`。
4. DNS 不用动（`www` 的 CNAME 仍指向 `shiyeshu.github.io`，外层还有 Cloudflare 代理）。

---

## 五、常见修改

| 想改什么 | 改哪里 |
| --- | --- |
| 站点标题 / 副标题 / 头像 / 简介 | `config/_default/languages.zh-cn.toml` |
| 配色（ocean / avocado / …）、浅色/深色默认 | `config/_default/params.toml` 的 `colorScheme`、`defaultAppearance` |
| 顶部菜单 | `config/_default/menus.zh-cn.toml` |
| 首页显示几篇、是否卡片 | `config/_default/params.toml` 的 `[homepage]` |
| 文章页目录 / 相关文章 / 评论开关 | `[article]` 与 `[comments.valine]` |
| 新文章地址规则 | `config/_default/hugo.toml` 的 `[permalinks]` |
| 每页文章数 | `[pagination] pagerSize` |
| 404 页 | 覆盖 `layouts/404.html`（当前用主题默认） |

### 搜索

Blowfish 自带全站搜索：按 <kbd>Ctrl</kbd>+<kbd>K</kbd>（或点顶部放大镜）打开。索引由 Hugo 根据 `[outputs] home = ["HTML","RSS","JSON"]` 生成，不需要第三方服务。

### 归档

旧站 `/archives/` 会跳到 `/post/`（`content/post/_index.md` 的 `aliases`），`/post/` 列表本身按年份分组，等同于归档页。

### 图片放哪

- 放进 `static/images/`，文章里写 `![说明](/images/xxx.png)`
- 旧站图片都按年份放在 `static/images/`，保持现状即可。

### 文章地址说明

39 篇文章在 front matter 里用 `url:` 字段**逐篇固定**了原地址（例如 `/2021/08/13/初探单域名单端口多服务web/`），不会被新的 `permalinks` 规则改变——这样搜索引擎收录、外部链接、旧评论都不会失效。**不要删这些 `url:` 字段。**

新文章不需要写 `url:`，走 `config/_default/hugo.toml` 的规则：`/年/月/日/文件名/`。

---

## 六、主题切换记录

- 2022 年：Hexo 5.4 + Kratos:Rebirth
- 2026-10：迁移到 Hugo（先 Stack，后根据预览对比选定 **Blowfish 浅色方案**）

## 七、迁移说明（2026-10）

- 原站是 **Hexo 5.4.0 + Kratos:Rebirth 主题**，仓库里只有生成的 HTML，原始 Markdown 未找到（本机全盘检索 3.2 万个 md，0 命中）。
- 旧站 35 篇文章、2 个独立页面由旧站 HTML **逐篇还原**为 Markdown，正文纯文本字符数与原文 100% 一致，代码块/图片/链接数量一致。
- 另从 xLog 存档中找回 **4 篇旧站没有的 2023 年文章**（`content/post/2023-*.md`）和 74 张 IPFS 图片，站内文章共 **39 篇**。
- 331 张旧站本地图片原样搬过来（47 MB），另有 74 张 IPFS 图片在 `static/images/xlog/`（7.9 MB）。
- 旧评论系统 Valine（LeanCloud）已接回，5 条历史评论按旧文章路径关联。
- 已知损失：
  - **25 张外链图片**原托管在 `img.sshuo.cc`（ATT&CK 一/五两篇），该域名已失效；其余 9 张同类图片已从 IPFS 找回。
  - 2 篇标注「（丢失文章）」的帖子本来就只有旧站的占位说明。
