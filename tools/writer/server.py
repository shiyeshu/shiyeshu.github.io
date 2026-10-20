#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""松鼠A的博客 —— 本地文章编写器（纯 Python 标准库，无第三方依赖）。

解决两件事：
  1) 截图粘贴/拖拽后自动存到 static/images/posts/<slug>/ 并插入 Markdown；
  2) 根据标题+正文自动推荐分类（网络安全 / 开发项目 / 日常随想）与标签。

用法：
    python tools/writer/server.py            # 默认 127.0.0.1:7311
    python tools/writer/server.py --port 7312 --open
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
import urllib.parse
import webbrowser
from collections import Counter
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ---------------------------------------------------------------- 路径与常量
TOOL_ROOT = Path(__file__).resolve().parent
SITE_ROOT = TOOL_ROOT.parents[1]            # blog/tools/writer -> blog
POSTS_DIR = SITE_ROOT / 'content' / 'post'
STATIC_DIR = SITE_ROOT / 'static'
IMAGES_ROOT = STATIC_DIR / 'images' / 'posts'
ASSETS_DIR = TOOL_ROOT / 'assets'
TZ = timezone(timedelta(hours=8))

CATEGORIES = ('网络安全', '开发项目', '日常随想')

# 分类关键词（命中即加权：标题 x5、正文 x1）
CATEGORY_KEYWORDS = {
    '网络安全': [
        '渗透', '漏洞', '攻防', '靶场', '免杀', '审计', 'xss', 'sql', 'sql注入', '提权',
        '木马', 'exp', 'exp编写', '0day', 'nday', 'poc', 'cve', '红队', 'red team', '内网',
        '横向', '后门', 'webshell', '反弹shell', 'getshell', '钓鱼', '溯源', '应急响应',
        'hw', 'hws', '蓝队', '蓝队', '安全', '加固', '基线', '挖洞', 'src', 'burp', 'nmap',
        'msf', 'metasploit', 'cobalt', 'cs上线', 'beacon', '域控', 'ntlm', '哈希', 'pass-the',
        '信息收集', 'fuzz', 'waf', 'ssrf', 'csrf', 'rce', 'csrf', '越权', '未授权', '反序列化',
        '蜜罐', '杀软', 'edr', 'av', '勒索', '僵尸网络', 'ddos', '密码学', '逆向',
    ],
    '开发项目': [
        '开发', '代码', '搭建', '部署', '服务器', '插件', '工具', '脚本', 'php', 'python',
        'c#', 'go', 'golang', 'java', 'js', 'javascript', 'typescript', '前端', '后端',
        '接口', 'api', '项目', '数据库', 'mysql', 'redis', 'sqlite', 'docker', 'nginx',
        'linux', 'windows', 'bat', 'powershell', 'git', 'github', '框架', '库', '自动化',
        '爬虫', '网站', '建站', 'hexo', 'hugo', '博客', '主题', '重构', '组件', '函数',
        '编译', '调试', '测试', 'cli', 'web', 'html', 'css', 'http', 'socket', '云服务器',
        'vps', '容器', '微服务', '架构', '算法', '数据结构',
    ],
    '日常随想': [
        '随笔', '随想', '生活', '心情', '日记', '纪念', '回忆', '想法', '吐槽', '感慨',
        '朋友', '大学', '毕业', '旅行', '游戏', '音乐', '电影', '读书', '最近', '今天',
        '记录一下', '碎碎念', '流水账', '一年', '生日', '过年', '假期', '周末',
    ],
}

# 标签映射：关键词 -> 标签（命中取前 5）
TAG_MAP = {
    '渗透测试': ['渗透', '渗透测试', '红队', 'src', '挖洞'],
    '漏洞复现': ['漏洞', '复现', 'cve', 'poc', '0day', 'nday', 'rce'],
    '代码审计': ['审计', '代码审计', '源码'],
    '内网渗透': ['内网', '横向', '域控', '域渗透', 'ntlm', '哈希'],
    'Web安全': ['xss', 'sql', 'ssrf', 'csrf', 'waf', '越权', '未授权', 'web安全', 'webshell'],
    '免杀': ['免杀', '杀软', 'edr', 'av', 'bypass'],
    '红蓝对抗': ['红蓝', '蓝队', 'hw', 'hws', '攻防'],
    '应急响应': ['应急响应', '溯源', '排查'],
    '提权': ['提权', 'privilege'],
    '靶场': ['靶场', 'vulnhub', 'vulnstack', '靶机'],
    'CTF': ['ctf', 'pwn', 'reverse', 'misc'],
    'Python': ['python', 'pip', 'flask', 'django'],
    'PHP': ['php', 'laravel', 'thinkphp'],
    'C#': ['c#', '.net', 'winform', 'wpf'],
    'Go': ['go', 'golang', 'gin'],
    'JavaScript': ['javascript', 'js', 'node', 'vue', 'react'],
    '建站': ['建站', 'hexo', 'hugo', 'wordpress', 'typecho', '博客'],
    '服务器': ['服务器', 'vps', '云服务器', '宝塔'],
    'Docker': ['docker', '容器', 'compose'],
    'Nginx': ['nginx', '反代', '反向代理'],
    'Linux': ['linux', 'centos', 'ubuntu', 'debian', 'shell', 'bash'],
    'Windows': ['windows', 'win7', 'win10', 'win11', '注册表'],
    'PowerShell': ['powershell', 'bat', 'cmd'],
    '数据库': ['数据库', 'mysql', 'redis', 'sqlite', 'sql'],
    '工具开发': ['工具', '插件', '脚本', 'cli'],
    '自动化': ['自动化', '爬虫', '定时任务'],
    '随笔': ['随笔', '随想', '碎碎念', '流水账'],
    '生活': ['生活', '日常', '心情', '假期', '周末'],
}

# 分类兜底标签
FALLBACK_TAGS = {
    '网络安全': ['网络安全'],
    '开发项目': ['开发'],
    '日常随想': ['随笔'],
}

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'}
MAX_UPLOAD = 20 * 1024 * 1024  # 20 MB


# ---------------------------------------------------------------- 工具函数
def now_tz() -> datetime:
    return datetime.now(TZ)


def slugify(title: str) -> str:
    """标题 -> 文件名 slug：保留中文，替换 Windows 非法字符，与现有文章风格一致。"""
    s = (title or '').strip()
    s = s.replace('\u3000', ' ')
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', '-', s)
    s = re.sub(r'\s+', ' ', s).strip(' .-_')
    return s or 'untitled'


def read_json(handler, limit=2 * 1024 * 1024) -> dict:
    length = int(handler.headers.get('Content-Length') or 0)
    if length <= 0 or length > limit:
        return {}
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode('utf-8'))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def header_text(handler, name: str, default: str = '') -> str:
    raw = handler.headers.get(name)
    if not raw:
        return default
    try:
        raw = raw.encode('latin-1').decode('utf-8')
    except Exception:
        pass
    if '%' in raw:
        raw = urllib.parse.unquote(raw)
    return raw.strip() or default


def json_response(handler, payload: dict, status: int = 200):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler, text: str, status: int = 200, ctype='text/plain; charset=utf-8'):
    body = text.encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', ctype)
    handler.send_header('Content-Length', str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def yaml_str(value: str) -> str:
    """JSON 双引号字符串即合法 YAML 双引号标量（中文原样保留）。"""
    return json.dumps(value or '', ensure_ascii=False)


def describe_from_body(body: str, limit: int = 80) -> str:
    """取正文首个有内容的“段落”（跳过标题/图片/列表符号/代码块），截断后作为 description。"""
    text = re.sub(r'```.*?```', '', body or '', flags=re.S)   # 去代码块
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(('#', '![', '>', '```', '---', '<!--')):
            continue                                          # 跳过标题/图片/引用/代码/分隔线
        line = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', line)      # 去行内图片
        line = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', line)  # 链接留文字
        line = re.sub(r'^[>*\-+]\s*', '', line)               # 列表符号
        line = re.sub(r'[*_`~]+', '', line)                   # 强调/行内代码
        line = re.sub(r'\s+', ' ', line).strip()
        if line:
            if len(line) > limit:
                return line[:limit].rstrip() + '…'
            return line
    return ''


# ---------------------------------------------------------------- 推荐引擎
def suggest(title: str, body: str) -> dict:
    title = title or ''
    body = body or ''
    text = (title + '\n' + body).lower()
    title_l = title.lower()

    # 分类打分
    scores = {c: 0 for c in CATEGORIES}
    for cat, words in CATEGORY_KEYWORDS.items():
        score = 0
        for w in words:
            wl = w.lower()
            n_title = title_l.count(wl)
            n_body = text.count(wl) - n_title
            if n_title:
                score += n_title * 5
            if n_body > 0:
                score += n_body
        scores[cat] = score
    best = max(scores, key=lambda c: scores[c])
    if scores[best] <= 0:
        best = '日常随想'

    # 标签打分
    counts = Counter()
    for tag, words in TAG_MAP.items():
        hit = 0
        for w in words:
            wl = w.lower()
            hit += title_l.count(wl) * 3 + max(0, text.count(wl) - title_l.count(wl))
        if hit:
            counts[tag] = hit
    tags = [t for t, _ in counts.most_common(5)]
    if not tags:
        tags = list(FALLBACK_TAGS[best])

    return {
        'category': best,
        'tags': tags,
        'scores': scores,
        'fallback': sum(scores.values()) == 0,
    }


# ---------------------------------------------------------------- 保存/上传
def save_post(data: dict) -> dict:
    title = (data.get('title') or '').strip()
    body = data.get('body') or ''
    if not title:
        raise ValueError('标题不能为空')
    if not body.strip():
        raise ValueError('正文不能为空')

    category = (data.get('category') or '').strip()
    if category in ('auto', '自动', '') or category not in CATEGORIES:
        category = suggest(title, body)['category']

    tags = data.get('tags') or []
    if isinstance(tags, str):
        tags = [t.strip() for t in re.split(r'[,，\s]+', tags) if t.strip()]
    tags = [str(t).strip() for t in tags if str(t).strip()]
    if not tags:
        tags = suggest(title, body)['tags']

    date_raw = (data.get('date') or '').strip()
    now = now_tz()
    date_str = now.strftime('%Y-%m-%d')
    if date_raw:
        m = re.match(r'^(\d{4})-(\d{2})-(\d{2})', date_raw)
        if not m:
            raise ValueError('日期格式应为 YYYY-MM-DD')
        date_str = '%s-%s-%s' % m.groups()
    dt = datetime.strptime(date_str, '%Y-%m-%d').replace(
        hour=now.hour, minute=now.minute, second=now.second, tzinfo=TZ)
    iso = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
    iso = iso[:-2] + ':' + iso[-2:]  # +0800 -> +08:00

    draft = bool(data.get('draft'))
    description = (data.get('description') or '').strip() or describe_from_body(body)
    slug = slugify(title)
    filename = '%s-%s.md' % (date_str, slug)
    target = POSTS_DIR / filename
    n = 2
    while target.exists():  # 同一天同名冲突时追加序号，绝不覆盖已有文章
        target = POSTS_DIR / ('%s-%s-%d.md' % (date_str, slug, n))
        n += 1
    filename = target.name

    fm = [
        '---',
        'title: %s' % yaml_str(title),
        'date: %s' % iso,
        'lastmod: %s' % iso,
        'description: %s' % yaml_str(description),
        'categories: [%s]' % ', '.join(yaml_str(c) for c in [category]),
        'tags: [%s]' % ', '.join(yaml_str(t) for t in tags),
        'draft: %s' % ('true' if draft else 'false'),
        '---',
        '',
    ]
    content = '\n'.join(fm) + body.rstrip('\n') + '\n'
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix('.md.tmp')
    tmp.write_text(content, encoding='utf-8', newline='\n')
    tmp.replace(target)
    return {
        'ok': True,
        'filename': filename,
        'path': str(target),
        'relative': str(target.relative_to(SITE_ROOT)).replace('\\', '/'),
        'slug': slug,
        'category': category,
        'tags': tags,
        'date': date_str,
        'draft': draft,
        'preview': 'http://localhost:1313/',
    }


def sniff_ext(data: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in IMAGE_EXTS:
        return ext
    head = data[:12]
    if head.startswith(b'\x89PNG'):
        return '.png'
    if head.startswith(b'\xff\xd8'):
        return '.jpg'
    if head.startswith(b'GIF8'):
        return '.gif'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return '.webp'
    if head.startswith(b'BM'):
        return '.bmp'
    return '.png'


def save_image(data: bytes, filename: str, slug: str) -> dict:
    if not data:
        raise ValueError('图片为空')
    if len(data) > MAX_UPLOAD:
        raise ValueError('图片超过 20MB')
    slug = slugify(slug) or 'untitled'
    ext = sniff_ext(data, filename)
    folder = IMAGES_ROOT / slug
    folder.mkdir(parents=True, exist_ok=True)
    stamp = now_tz().strftime('%Y%m%d-%H%M%S')
    n = 1
    while True:
        name = '%s-%02d%s' % (stamp, n, ext)
        target = folder / name
        if not target.exists():
            break
        n += 1
    tmp = folder / (name + '.tmp')
    tmp.write_bytes(data)
    tmp.replace(target)
    url_path = '/images/posts/%s/%s' % (urllib.parse.quote(slug), urllib.parse.quote(name))
    return {
        'ok': True,
        'url': url_path,
        'name': name,
        'slug': slug,
        'path': str(target),
        'relative': str(target.relative_to(SITE_ROOT)).replace('\\', '/'),
        'size': len(data),
    }


# ---------------------------------------------------------------- HTTP
class WriterHandler(BaseHTTPRequestHandler):
    server_version = 'Writer/1.0'
    protocol_version = 'HTTP/1.1'

    # 静默掉逐条访问日志（保留错误）
    def log_message(self, fmt, *args):
        sys.stderr.write('[%s] %s\n' % (self.log_date_time_string(), fmt % args))

    # ---------------- GET ----------------
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ('/', '/index.html'):
            return self.serve_file(TOOL_ROOT / 'writer.html', 'text/html; charset=utf-8')
        if path.startswith('/assets/'):
            return self.serve_file(self.safe_join(ASSETS_DIR, path[len('/assets/'):]))
        if path.startswith('/images/'):
            return self.serve_file(self.safe_join(STATIC_DIR, path.lstrip('/')))
        if path == '/api/health':
            return json_response(self, {
                'ok': True,
                'site': str(SITE_ROOT),
                'posts': len(list(POSTS_DIR.glob('*.md'))) if POSTS_DIR.exists() else 0,
                'images_root': str(IMAGES_ROOT),
                'time': now_tz().strftime('%Y-%m-%d %H:%M:%S%z'),
                'categories': list(CATEGORIES),
            })
        return text_response(self, 'Not Found: %s' % path, 404)

    def safe_join(self, root: Path, rel: str):
        rel = urllib.parse.unquote(rel).lstrip('/')
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            return None
        return candidate

    def serve_file(self, path, ctype=None):
        if path is None or not path.exists() or not path.is_file():
            return text_response(self, 'Not Found', 404)
        if ctype is None:
            ctype = self.guess_type(path)
        data = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def guess_type(path: Path) -> str:
        ext = path.suffix.lower()
        return {
            '.html': 'text/html; charset=utf-8',
            '.js': 'application/javascript; charset=utf-8',
            '.css': 'text/css; charset=utf-8',
            '.json': 'application/json; charset=utf-8',
            '.svg': 'image/svg+xml',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.ico': 'image/x-icon',
            '.woff2': 'font/woff2',
        }.get(ext, 'application/octet-stream')

    # ---------------- POST ----------------
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        try:
            if path == '/api/suggest':
                data = read_json(self)
                return json_response(self, suggest(data.get('title', ''), data.get('body', '')))
            if path == '/api/upload':
                return self.handle_upload()
            if path == '/api/save':
                data = read_json(self)
                return json_response(self, save_post(data))
            if path == '/api/publish':
                return self.handle_publish()
            return text_response(self, 'Not Found: %s' % path, 404)
        except ValueError as exc:
            return json_response(self, {'ok': False, 'error': str(exc)}, 400)
        except Exception as exc:  # pragma: no cover - 兜底
            return json_response(self, {'ok': False, 'error': '%s: %s' % (type(exc).__name__, exc)}, 500)

    def handle_upload(self):
        length = int(self.headers.get('Content-Length') or 0)
        if length <= 0:
            raise ValueError('缺少图片数据')
        if length > MAX_UPLOAD:
            raise ValueError('图片超过 20MB')
        data = self.rfile.read(length)
        filename = header_text(self, 'X-Filename', 'pasted.png')
        slug = header_text(self, 'X-Slug', 'untitled')
        return json_response(self, save_image(data, filename, slug))

    def handle_publish(self):
        """调用仓库根 deploy.ps1（会 git push），前端需二次确认。"""
        import subprocess
        script = SITE_ROOT / 'deploy.ps1'
        if not script.exists():
            raise ValueError('找不到 deploy.ps1')
        proc = subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)],
            cwd=str(SITE_ROOT), capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=300)
        out = (proc.stdout or '') + (('\n[stderr]\n' + proc.stderr) if proc.stderr else '')
        return json_response(self, {'ok': proc.returncode == 0, 'code': proc.returncode, 'output': out[-8000:]})


# ---------------------------------------------------------------- 入口
def main(argv=None):
    ap = argparse.ArgumentParser(description='松鼠A的博客 本地文章编写器')
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=7311)
    ap.add_argument('--open', action='store_true', help='启动后自动打开浏览器')
    args = ap.parse_args(argv)

    httpd = ThreadingHTTPServer((args.host, args.port), WriterHandler)
    url = 'http://%s:%d/' % (args.host, args.port)
    print('=' * 64)
    print('  松鼠A的博客 · 文章编写器')
    print('  站点根目录：%s' % SITE_ROOT)
    print('  文章目录：  %s' % POSTS_DIR)
    print('  图片目录：  %s' % IMAGES_ROOT)
    print('  服务地址：  %s   (Ctrl+C 停止)' % url)
    print('=' * 64)
    if args.open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止。')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    main()
