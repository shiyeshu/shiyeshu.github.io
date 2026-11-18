#!/usr/bin/env python3
"""触发 GitHub Pages 构建并等待完成。

用途：站点以 gh-pages 分支发布（legacy Pages），推送后调用本脚本确认线上构建完成。
凭据复用本机 git 凭据（git credential fill），不需要手动填 token。

用法：
    python tools/pages_build.py            # 触发并等待，最多 5 分钟
    python tools/pages_build.py --status   # 只查看最近一次构建状态
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

OWNER = "shiyeshu"
REPO = "shiyeshu.github.io"
API = "https://api.github.com"


def get_token() -> str:
    env = dict(os.environ)
    env["GCM_INTERACTIVE"] = "never"
    env["GIT_TERMINAL_PROMPT"] = "0"
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, env=env, timeout=60,
    )
    if p.returncode != 0:
        raise SystemExit("无法读取 git 凭据：" + p.stderr.strip()[:160])
    data = dict(line.split("=", 1) for line in p.stdout.splitlines() if "=" in line)
    token = data.get("password", "")
    if not token:
        raise SystemExit("git 凭据里没有 github.com 的 token")
    return token


def api(token: str, method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "dsh-pages-build",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            err = json.loads(raw)
        except Exception:
            err = raw[:300].decode("utf-8", "replace")
        return e.code, err


def latest(token: str) -> dict:
    _, b = api(token, "GET", f"/repos/{OWNER}/{REPO}/pages/builds/latest")
    return b or {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true", help="只查看最近一次构建")
    ap.add_argument("--timeout", type=int, default=300, help="等待秒数，默认 300")
    args = ap.parse_args()

    token = get_token()
    if not args.status:
        st, body = api(token, "POST", f"/repos/{OWNER}/{REPO}/pages/builds")
        print(f"触发构建：HTTP {st}")
        if st >= 300:
            print(json.dumps(body, ensure_ascii=False)[:300])

    deadline = time.time() + args.timeout
    last = None
    while time.time() < deadline:
        b = latest(token)
        status = b.get("status")
        commit = str(b.get("commit") or "")[:8]
        if status != last:
            print(f"Pages 构建：{status} ({commit})", flush=True)
            last = status
        if status == "built":
            print("构建完成：https://www.sshuo.cc/")
            return 0
        if status == "errored":
            err = (b.get("error") or {}).get("message")
            print(f"构建失败：{err}")
            return 1
        time.sleep(8)
    print("等待超时，请到 GitHub → Settings → Pages 查看构建状态")
    return 2


if __name__ == "__main__":
    sys.exit(main())
