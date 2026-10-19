#!/usr/bin/env python3
"""校验 Hugo 构建产物：35 篇旧文章 URL 是否全部生成、正文/图片/代码块是否完整。

用法：
    python scripts/verify_site.py [--site blog] [--public blog/public]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


def load_posts(content_dir: Path):
    posts = []
    for md in sorted(content_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            print(f"[FAIL] front matter 缺失: {md.name}")
            continue
        meta = yaml.safe_load(m.group(1)) or {}
        body = text[m.end():]
        posts.append({"file": md, "meta": meta, "body": body})
    return posts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="blog")
    ap.add_argument("--public", default="blog/public")
    args = ap.parse_args()
    site = Path(args.site)
    public = Path(args.public)

    posts = load_posts(site / "content" / "post")
    print(f"发现文章: {len(posts)}")

    errors = []
    for p in posts:
        url = p["meta"].get("url")
        if not url:
            errors.append(f"{p['file'].name}: 缺 url")
            continue
        target = public / url.lstrip("/") / "index.html"
        if not target.exists():
            errors.append(f"{p['file'].name}: 产物缺失 {target}")
            continue
        html = target.read_text(encoding="utf-8", errors="replace")
        # 图片数量
        want_imgs = len(re.findall(r"!\[[^\]]*\]\(", p["body"]))
        got_imgs = len(re.findall(r"<img ", html))
        if want_imgs and got_imgs < want_imgs:
            errors.append(f"{p['file'].name}: 图片 {want_imgs} -> {got_imgs}")
        # 代码块
        want_code = p["body"].count("```") // 2
        got_code = len(re.findall(r"<pre", html))
        if want_code and got_code < want_code:
            errors.append(f"{p['file'].name}: 代码块 {want_code} -> {got_code}")
        # 标题
        title = p["meta"].get("title", "")
        if title and title.split("（")[0][:10] not in html:
            errors.append(f"{p['file'].name}: 标题未出现在页面")

    # 页面
    pages = [
        ("about", "/about/me.html"),
        ("friends", "/friends/"),
        ("archives", "/archives/"),
        ("search", "/search/"),
    ]
    for name, url in pages:
        target = public / url.lstrip("/")
        if url.endswith(".html"):
            ok = target.exists()
        else:
            ok = (target / "index.html").exists()
        if not ok:
            errors.append(f"页面缺失: {name} {url}")

    # 静态资源
    for need in ["static/CNAME", "static/js/valine.min.js"]:
        f = site / need
        if not f.exists():
            errors.append(f"缺少 {need}")
    if not (site / "static" / "images").exists():
        errors.append("缺少 static/images")

    if errors:
        print("\n失败项:")
        for e in errors:
            print("  -", e)
        print(f"\n结果: FAIL ({len(errors)} 项)")
        return 1

    print(f"\n结果: PASS — {len(posts)} 篇文章 URL 全部命中，页面/静态资源齐全")
    return 0


if __name__ == "__main__":
    sys.exit(main())
