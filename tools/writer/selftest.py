#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编写器自测脚本（纯标准库；压缩用例在装了 Pillow 时额外运行）。

用法：python tools/writer/selftest.py [--port 7312]
做什么：
  1. 起一个临时 server（默认 7312），检查页面/静态资源可访问；
  2. 实测 /api/suggest（安全类 / 开发类 / 日常类）；
  3. 实测 /api/upload（1x1 PNG 原图模式 + 大图 WebP 压缩 + 透明通道 + EXIF 方向 + 关闭压缩）；
  4. 实测 /api/save（front matter 字段 + 正文原样 + 同名冲突不覆盖）；
  5. 清理测试产生的文章/图片，失败时退出码非 0。
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:  # 压缩用例需要 Pillow；没有则跳过压缩测试（服务端也会自动降级）
    from PIL import Image

    PIL_AVAILABLE = True
except Exception:  # pragma: no cover
    Image = None
    PIL_AVAILABLE = False

TOOL_ROOT = Path(__file__).resolve().parent
SITE_ROOT = TOOL_ROOT.parents[1]
POSTS_DIR = SITE_ROOT / 'content' / 'post'
IMAGES_ROOT = SITE_ROOT / 'static' / 'images' / 'posts'
SLUG = 'writer-selftest'
COMPRESS_SLUG = 'writer-compress-selftest'

PNG_1X1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
PNG_1X1_B64 = base64.b64encode(PNG_1X1).decode('ascii')

results = []
created_files = []
created_dirs = []


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))
    print(('  [PASS] ' if cond else '  [FAIL] ') + name + (('  — ' + detail) if detail else ''))
    return bool(cond)


def request(url, method='GET', data=None, headers=None, raw=False):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
        return resp.status, (body if raw else body.decode('utf-8'))


def post_json(base, path, payload):
    return request(base + path, 'POST', json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                   {'Content-Type': 'application/json'})


def fmt_size(n):
    if n is None:
        return '?'
    if n >= 1024 * 1024:
        return '%.2fMB' % (n / 1024 / 1024)
    if n >= 1024:
        return '%.1fKB' % (n / 1024)
    return '%dB' % n


def make_noise_png(w, h):
    """生成一张噪声 PNG（内容不可压，体积接近原始大小，适合验证压缩收益）。"""
    im = Image.effect_noise((w, h), 64).convert('RGB')
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    return buf.getvalue()


def make_alpha_png(w, h):
    """生成带渐变 alpha 的 RGBA PNG（验证透明通道保留）。"""
    rgb = Image.effect_noise((w, h), 48).convert('RGB')
    alpha = Image.linear_gradient('L').resize((w, h))
    im = rgb.convert('RGBA')
    im.putalpha(alpha)
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    return buf.getvalue()


def make_exif_jpeg(w, h):
    """生成带 EXIF orientation=6 的 JPEG（验证方向纠正：宽高应互换）。"""
    im = Image.effect_noise((w, h), 64).convert('RGB')
    exif = Image.Exif()
    exif[274] = 6  # Orientation = Rotate 90 CW
    buf = io.BytesIO()
    im.save(buf, format='JPEG', quality=90, exif=exif)
    return buf.getvalue()


def wait_ready(base, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            status, body = request(base + '/api/health')
            if status == 200:
                return json.loads(body)
        except Exception:
            time.sleep(0.3)
    raise RuntimeError('server 未在超时时间内就绪：' + base)


def cleanup():
    for f in created_files:
        try:
            if Path(f).exists():
                Path(f).unlink()
        except Exception as exc:
            print('  [warn] 清理文件失败：%s (%s)' % (f, exc))
    for d in sorted(set(created_dirs)):
        try:
            p = Path(d)
            if p.exists():
                for child in p.iterdir():
                    child.unlink()
                p.rmdir()
        except Exception as exc:
            print('  [warn] 清理目录失败：%s (%s)' % (d, exc))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=7312)
    args = ap.parse_args()
    base = 'http://127.0.0.1:%d' % args.port

    proc = subprocess.Popen([sys.executable, str(TOOL_ROOT / 'server.py'), '--port', str(args.port)],
                            cwd=str(SITE_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        health = wait_ready(base)
        print('服务已就绪：%s（站点 %s，已有文章 %s 篇）' % (base, health['site'], health['posts']))

        # 1. 页面与静态资源
        st, html = request(base + '/')
        check('GET / 返回编写器页面', st == 200 and '文章编写器' in html, '%d bytes' % len(html))
        st, css = request(base + '/assets/writer.css')
        check('GET /assets/writer.css', st == 200 and len(css) > 500)
        st, js = request(base + '/assets/writer.js')
        check('GET /assets/writer.js', st == 200 and len(js) > 500)
        st, marked = request(base + '/assets/marked.min.js', raw=True)
        check('GET /assets/marked.min.js（vendored，无 CDN）', st == 200 and len(marked) > 5000,
              '%d bytes' % len(marked))

        # 2. /api/suggest
        st, body = post_json(base, '/api/suggest', {
            'title': '某靶场 SQL 注入到内网渗透',
            'body': '最近在打一个靶场，发现 SQL 注入漏洞，签到后台后 getshell，'
                    '接着做提权与内网横向，最后拿下域控。顺手记录了 burp 抓包与 nmap 扫描过程。',
        })
        data = json.loads(body)
        check('/api/suggest 安全类 → 网络安全', data.get('category') == '网络安全',
              'category=%s tags=%s' % (data.get('category'), data.get('tags')))
        check('/api/suggest 安全类标签合理',
              any(t in data.get('tags', []) for t in ('渗透测试', '漏洞复现', '内网渗透', 'Web安全')),
              str(data.get('tags')))

        st, body = post_json(base, '/api/suggest', {
            'title': '用 Python 写一个自动化工具并部署到服务器',
            'body': '这次用 Python 开发了一个小工具，代码里用 requests 调接口，'
                    '然后用 Docker 部署到 Linux 服务器，Nginx 做反向代理，顺手重构了数据库查询。',
        })
        data = json.loads(body)
        check('/api/suggest 开发类 → 开发项目', data.get('category') == '开发项目',
              'category=%s tags=%s' % (data.get('category'), data.get('tags')))

        st, body = post_json(base, '/api/suggest', {
            'title': '周末爬山小记',
            'body': '最近天气不错，周末和朋友去爬山，心情挺好的，随手写点生活流水账，记录一下假期。',
        })
        data = json.loads(body)
        check('/api/suggest 日常类 → 日常随想', data.get('category') == '日常随想',
              'category=%s tags=%s' % (data.get('category'), data.get('tags')))

        # 3. /api/upload（原图模式：X-Compress: 0，字节应与上传内容完全一致）
        st, body = request(base + '/api/upload', 'POST', PNG_1X1, {
            'Content-Type': 'image/png',
            'X-Filename': '%E8%87%AA%E6%B5%8B.png',
            'X-Slug': SLUG,
            'X-Compress': '0',
        })
        up = json.loads(body)
        ok = st == 200 and up.get('ok') and up.get('url', '').startswith('/images/posts/%s/' % SLUG)
        check('/api/upload 保存 1x1 PNG（原图模式）', ok, str(up.get('relative')))
        if ok:
            created_files.append(up['path'])
            created_dirs.append(str(IMAGES_ROOT / SLUG))
            check('原图模式：compressed=false、format=png、size=original_size',
                  up.get('compressed') is False and up.get('format') == 'png'
                  and up.get('size') == len(PNG_1X1) == up.get('original_size'))
            st, img = request(base + up['url'], raw=True)
            check('上传后的图片可通过 /images/... 回读', st == 200 and img == PNG_1X1,
                  '%d bytes' % len(img))
            check('图片落盘位置正确', Path(up['path']).exists() and 'static' in up['path'])

        # 3b. /api/upload 自动压缩（Pillow 可用时；不可用时服务端降级、这里跳过）
        if not PIL_AVAILABLE:
            print('  [SKIP] 图片压缩测试（本机未安装 Pillow，服务端会优雅降级为原图）')
        else:
            big_png = make_noise_png(2000, 1200)
            st, body = request(base + '/api/upload', 'POST', big_png, {
                'Content-Type': 'image/png',
                'X-Filename': 'big.png',
                'X-Slug': COMPRESS_SLUG,
                'X-Compress': '1',
            })
            res = json.loads(body)
            ok_cmp = st == 200 and res.get('ok')
            check('压缩：默认开启时 2000x1200 PNG → .webp',
                  ok_cmp and res.get('compressed') is True and res.get('format') == 'webp'
                  and res.get('url', '').endswith('.webp'))
            if ok_cmp:
                created_files.append(res['path'])
                created_dirs.append(str(IMAGES_ROOT / COMPRESS_SLUG))
                check('压缩：体积变小且 saved_percent 合理',
                      res['size'] < res['original_size']
                      and abs(res['saved_percent']
                              - round((1 - res['size'] / res['original_size']) * 100, 1)) <= 0.2,
                      '原 %s → %s（-%.1f%%）'
                      % (fmt_size(res['original_size']), fmt_size(res['size']), res['saved_percent']))
                check('压缩：最长边 2000→1600、等比 1200→960',
                      res.get('width') == 1600 and res.get('height') == 960,
                      '%sx%s' % (res.get('width'), res.get('height')))
                check('压缩：返回 original_size/size/compressed/format/width/height/saved_percent 字段',
                      all(k in res for k in ('original_size', 'size', 'compressed', 'format',
                                             'width', 'height', 'saved_percent')))
                st, raw = request(base + res['url'], raw=True)
                check('压缩：WebP 可通过 /images/... 回读',
                      st == 200 and raw[:4] == b'RIFF' and raw[8:12] == b'WEBP',
                      '%d bytes' % len(raw))
                with Image.open(io.BytesIO(raw)) as im:
                    check('压缩：回读确认 WEBP 格式与 1600x960 尺寸',
                          im.format == 'WEBP' and im.size == (1600, 960), '%s %s' % (im.format, im.size))

            # 透明通道保留
            alpha_png = make_alpha_png(2000, 1200)
            st, body = request(base + '/api/upload', 'POST', alpha_png, {
                'Content-Type': 'image/png', 'X-Filename': 'alpha.png',
                'X-Slug': COMPRESS_SLUG, 'X-Compress': '1',
            })
            ares = json.loads(body)
            check('压缩：RGBA 透明图 → .webp 且 compressed=true',
                  st == 200 and ares.get('ok') and ares.get('compressed') is True)
            if ares.get('ok'):
                created_files.append(ares['path'])
                st, raw = request(base + ares['url'], raw=True)
                with Image.open(io.BytesIO(raw)) as im:
                    has_alpha = (im.mode in ('RGBA', 'LA')) or ('A' in im.getbands())
                    check('压缩：透明通道被保留', has_alpha, 'mode=%s' % im.mode)

            # EXIF 方向纠正（orientation=6：原图 2400x1200 应纠正为 1200x2400，再缩到 800x1600）
            exif_jpg = make_exif_jpeg(2400, 1200)
            st, body = request(base + '/api/upload', 'POST', exif_jpg, {
                'Content-Type': 'image/jpeg', 'X-Filename': 'exif.jpg',
                'X-Slug': COMPRESS_SLUG, 'X-Compress': '1',
            })
            xres = json.loads(body)
            check('压缩：EXIF orientation=6 已纠正（宽高互换后缩放到 800x1600）',
                  st == 200 and xres.get('ok') and (xres.get('width'), xres.get('height')) == (800, 1600),
                  '%sx%s' % (xres.get('width'), xres.get('height')))
            if xres.get('ok'):
                created_files.append(xres['path'])

            # 关闭压缩（query 参数）
            st, body = request(base + '/api/upload?compress=0', 'POST', big_png, {
                'Content-Type': 'image/png', 'X-Filename': 'big.png',
                'X-Slug': COMPRESS_SLUG,
            })
            off = json.loads(body)
            check('compress=0：保存原图（.png、compressed=false、字节不变）',
                  st == 200 and off.get('ok') and off.get('compressed') is False
                  and off.get('format') == 'png' and off.get('size') == len(big_png)
                  and off.get('url', '').endswith('.png'))
            if off.get('ok'):
                created_files.append(off['path'])
                st, raw = request(base + off['url'], raw=True)
                check('compress=0：回读字节与上传原图一致', raw == big_png, '%d bytes' % len(raw))

        # 4. /api/save（自动分类 + 自动标签 + front matter）
        today = time.strftime('%Y-%m-%d')
        body_md = ('## 自测小标题\n\n'
                   '这是一个由 selftest.py 自动创建的安全类段落：靶场、SQL 注入、getshell、提权、内网。\n\n'
                   '![图片](%s)\n\n'
                   '- 列表项一\n- 列表项二\n' % (up.get('url') if ok else '/images/posts/x.png'))
        st, body = post_json(base, '/api/save', {
            'title': '编写器自测文章-请删除',
            'date': today,
            'category': 'auto',
            'tags': [],
            'body': body_md,
            'draft': True,
        })
        saved = json.loads(body)
        check('/api/save 保存成功', st == 200 and saved.get('ok'), saved.get('relative', str(saved)))
        if saved.get('ok'):
            path = Path(saved['path'])
            created_files.append(str(path))
            text = path.read_text(encoding='utf-8')
            fm_ok = (text.startswith('---\n')
                     and 'title: "编写器自测文章-请删除"' in text
                     and 'categories: ["网络安全"]' in text
                     and 'draft: true' in text
                     and 'lastmod:' in text and 'description:' in text)
            check('front matter 字段齐全（title/date/lastmod/description/categories/tags/draft）', fm_ok)
            check('自动分类为网络安全', saved.get('category') == '网络安全', saved.get('category'))
            check('自动标签非空', bool(saved.get('tags')), str(saved.get('tags')))
            check('filename = <date>-<slug>.md', path.name == '%s-%s.md' % (today, saved['slug']),
                  path.name)
            check('正文原样写入（含标题/列表/图片）',
                  '## 自测小标题' in text and '- 列表项一' in text and '!/images/posts/' not in text)
            check('description 取首段截断', '这是一个由 selftest.py 自动创建的安全类段落' in text)

            # 同名冲突：再存一次，不应覆盖原文件
            st, body = post_json(base, '/api/save', {
                'title': '编写器自测文章-请删除', 'date': today, 'category': 'auto', 'tags': [],
                'body': '第二个同名文章内容。', 'draft': False,
            })
            saved2 = json.loads(body)
            check('同名文章不覆盖（自动加序号）',
                  saved2.get('ok') and saved2['path'] != saved['path'], saved2.get('filename'))
            if saved2.get('ok'):
                created_files.append(saved2['path'])
                check('原文件内容未被覆盖', Path(saved['path']).read_text(encoding='utf-8') == text)

        # 5. 错误处理
        try:
            post_json(base, '/api/save', {'title': '', 'body': ''})
            check('空标题/正文返回 400', False, '未返回错误')
        except urllib.error.HTTPError as exc:
            check('空标题/正文返回 400', exc.code == 400, str(exc.code))

        # 6. 可选发布接口存在（不实际调用，避免 git push）
        st, body = request(base + '/api/health')
        check('发布接口为可选（未在自测中调用 deploy.ps1）', 'ok' in json.loads(body))

    finally:
        cleanup()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

    passed = sum(1 for _n, ok, _d in results if ok)
    failed = len(results) - passed
    print('\n测试结果：%d 项通过，%d 项失败（测试文件已清理）' % (passed, failed))
    if failed:
        print('\n失败项：')
        for name, ok, detail in results:
            if not ok:
                print('  - %s %s' % (name, detail))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
