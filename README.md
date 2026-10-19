# 松鼠A的博客

基于 [Hugo](https://gohugo.io) + [Stack 主题](https://github.com/CaiJimmy/hugo-theme-stack) 的静态博客，部署在 GitHub Pages，绑定域名 **https://www.sshuo.cc**。

---

## 一、写一篇新文章（日常流程）

```bash
# 1. 新建文章（文件名就是将来的 URL 的一部分，建议用中文标题或英文 slug）
hugo new post/我的新文章.md

# 2. 编辑 content/post/我的新文章.md，写好正文
#    开头的 front matter 示例：
#    ---
#    title: "我的新文章"
#    date: 2026-10-20T10:00:00+08:00
#    draft: true          # 写的时候保持 true，发布前改成 false
#    description: "一句话摘要，会用于搜索结果和社交分享"
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

推送后 GitHub Actions 会自动构建并发布，约 1~2 分钟后线上可见（可在仓库 **Actions** 页面看进度，**Deployments** 看结果）。

> 不想每次敲命令：也可以在 GitHub 网页上直接进 `content/post/` → **Add file → Create new file**，粘贴带 front matter 的 Markdown，Commit 即可发布（`draft` 记得写 `false`）。

---

## 二、本地环境准备（换电脑时看）

只需装一个 Hugo 可执行文件，不需要 Node.js / npm / Ruby。

1. 下载 **Hugo extended**（Windows amd64）：<https://github.com/gohugoio/hugo/releases>
   文件名形如 `hugo_extended_0.168.0_windows-amd64.zip`
2. 解压得到 `hugo.exe`，放到 `C:\Windows` 或任意目录并加入 PATH；或直接在该目录运行
3. 验证：`hugo version`（应显示 `...extended...`）
4. 克隆本站：`git clone https://github.com/shiyeshu/shiyeshu.github.io`
5. 进入目录运行 `hugo server -D`

> 本仓库已内置主题（`themes/Stack`），**不需要** `git submodule`，克隆即用、离线也能构建。

---

## 三、目录结构

```
.
├── hugo.toml                 # 站点配置（标题、菜单、评论、分页、URL 规则…）
├── content/
│   ├── post/                 # ★ 所有文章（Markdown）
│   └── page/                 # 独立页面：关于、友链、归档、搜索
├── static/
│   ├── images/               # 站点图片（旧站图片已全部在此，按年份分目录）
│   ├── js/valine.min.js      # 评论组件（本地化，不依赖 CDN）
│   └── CNAME                 # 自定义域名，内容为 www.sshuo.cc
├── themes/Stack/             # 主题（已内置，可不管）
├── layouts/_markup/render-image.html   # 站点级图片渲染覆盖（外链图片不做下载处理）
├── layouts/_partials/comments/provider/valine.html  # 评论模板
├── scripts/verify_site.py    # 构建后自检：35 篇旧文 URL 是否都在
├── archetypes/post.md        # `hugo new post/xxx.md` 的模板
└── .github/workflows/hugo.yml # 自动构建 + 发布到 GitHub Pages
```

---

## 四、部署（GitHub Pages）

### 首次切换（重要：只需做一次）

旧仓库里现在放的是 Hexo 生成的成品 HTML。换成 Hugo 源码后需要：

1. **备份旧站**（保命）：在仓库 **Branches** 里新建分支 `legacy-hexo-2022` 指向旧的 `master`，不要删除旧提交。
2. 把本目录内容推到仓库 **`main`** 分支（覆盖旧的成品文件）。
3. 仓库 **Settings → Pages**：
   - **Source** 选 **GitHub Actions**（不要选 "Deploy from a branch"）
   - **Custom domain** 填 `www.sshuo.cc`，勾选 **Enforce HTTPS**
4. 推送后到 **Actions** 看 `Deploy Hugo site to GitHub Pages` 是否成功。
5. 域名解析保持原样即可（`www` → CNAME 到 `shiyeshu.github.io`）。

> 为什么用 Actions：源码和成品分离，成品不再进仓库历史，仓库体积小、也不会出现"忘记手动生成"的问题。

### 日常发布

`git push` 即自动发布。手动重跑：**Actions → Deploy Hugo site to GitHub Pages → Run workflow**。

---

## 五、常见修改

| 想改什么 | 改哪里 |
| --- | --- |
| 站点标题 / 副标题 / 头像 / 表情 | `hugo.toml` 的 `title`、`[params.sidebar]` |
| 页脚版权、起始年份 | `[params.footer]` |
| 顶部菜单 | `content/page/*/index.md` 的 `menu.main`（weight 越小越靠前） |
| 文章地址规则（新文章） | `[permalinks] post = "/:year/:month/:day/:slug/"` |
| 每页文章数 | `[pagination] pagerSize` |
| 深色模式 | `[params.colorScheme] default = "auto"/"light"/"dark"` |
| 评论 | `[params.comments]`；旧站 LeanCloud 应用仍在，保留即可 |
| 首页右侧小部件 | `[params.widgets] homepage` |
| 404 页 | 覆盖 `layouts/404.html`（当前用主题默认） |

### 图片放哪

- 放进 `static/images/`，文章里写 `![说明](/images/xxx.png)`
- 也可以每篇文章一个文件夹（page bundle），但旧站图片都按年份放在 `static/images/`，保持现状最省事。

### 文章地址说明

35 篇旧文章在 front matter 里用 `url:` 字段**逐篇固定**了原地址（例如 `/2021/08/13/初探单域名单端口多服务web/`），不会被新的 `permalinks` 规则改变——这是为了不让搜索引擎收录、外部链接、旧评论失效。**不要删这些 `url:` 字段。**

新文章不需要写 `url:`，走 `hugo.toml` 的规则：`/年/月/日/文件名/`。

---

## 六、迁移说明（2026-10）

- 原站是 **Hexo 5.4.0 + Kratos:Rebirth 主题**，仓库里只有生成的 HTML，原始 Markdown 未找到（本机全盘检索 3.2 万个 md，0 命中）。
- 旧站 35 篇文章、2 个独立页面由旧站 HTML **逐篇还原**为 Markdown，正文纯文本字符数与原文 100% 一致，代码块/图片/链接数量一致。
- 另从 xLog 存档中找回 **4 篇旧站没有的 2023 年文章**（见 `content/post/2023-*.md`）和 74 张 IPFS 图片，站内文章共 **39 篇**。
- 331 张旧站本地图片原样搬过来（47 MB），另有 74 张 IPFS 图片在 `static/images/xlog/`（7.9 MB）。
- 旧评论系统 Valine（LeanCloud）原应用仍可读，已接回，评论数 5 条，按旧文章路径关联。
- 已知损失：
  - **25 张外链图片**原托管在 `img.sshuo.cc`（ATT&CK 一/五两篇），该域名已失效，暂无来源可补；其余 9 张同类图片已从 IPFS 找回。
  - 2 篇标注「（丢失文章）」的帖子本来就只有旧站的占位说明。
