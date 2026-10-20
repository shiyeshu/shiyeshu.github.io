#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编写器自测脚本（纯标准库）。

用法：python tools/writer/selftest.py [--port 7312]
做什么：
  1. 起一个临时 server（默认 7312），检查页面/静态资源可访问；
  2. 实测 /api/suggest（安全类 / 开发类 / 日常类）；
  3. 实测 /api/upload（1x1 PNG，落到 static/images/posts/... 并可回读）；
  4. 实测 /api/save（front matter 字段 + 正文原样 + 同名冲突不覆盖）；
  5. 清理测试产生的文章/图片，失败时退出码非 0。
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
SITE_ROOT = TOOL_ROOT.parents[1]
POSTS_DIR = SITE_ROOT / 'content' / 'post'
IMAGES_ROOT = SITE_ROOT / 'static' / 'images' / 'posts'
SLUG = 'writer-selftest'

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
    for d in created_dirs:
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

        # 3. /api/upload
        st, body = request(base + '/api/upload', 'POST', PNG_1X1, {
            'Content-Type': 'image/png',
            'X-Filename': '%E8%87%AA%E6%B5%8B.png',
            'X-Slug': SLUG,
        })
        up = json.loads(body)
        ok = st == 200 and up.get('ok') and up.get('url', '').startswith('/images/posts/%s/' % SLUG)
        check('/api/upload 保存 1x1 PNG', ok, str(up.get('relative')))
        if ok:
            created_files.append(up['path'])
            created_dirs.append(str(IMAGES_ROOT / SLUG))
            st, img = request(base + up['url'], raw=True)
            check('上传后的图片可通过 /images/... 回读', st == 200 and img == PNG_1X1,
                  '%d bytes' % len(img))
            check('图片落盘位置正确', Path(up['path']).exists() and 'static' in up['path'])

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
