# =============================================================================
# 发布脚本：构建 Hugo 站点并推送到 gh-pages 分支
# 用途：当前 GitHub Pages 使用「gh-pages 分支」方式部署（GitHub Actions 故障期间
#       的应急方案）。等 Actions 恢复后，可切回 workflow 模式，届时直接 git push
#       即可自动发布，不需要运行本脚本。
#
# 用法（在仓库根目录）：
#   .\deploy.ps1
# =============================================================================
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 1) 找 Hugo（优先 PATH，其次本地 tools 目录）
$hugo = Get-Command hugo -ErrorAction SilentlyContinue
if ($hugo) {
    $hugoExe = "hugo"
} elseif (Test-Path "..\tools\hugo167\hugo.exe") {
    $hugoExe = "..\tools\hugo167\hugo.exe"
} elseif (Test-Path "..\tools\hugo\hugo.exe") {
    $hugoExe = "..\tools\hugo\hugo.exe"
} else {
    throw "找不到 hugo.exe，请先安装 Hugo extended 0.167.0 并加入 PATH"
}

Write-Host "==> 构建站点" -ForegroundColor Cyan
& $hugoExe --gc --minify
if ($LASTEXITCODE -ne 0) { throw "Hugo 构建失败" }

# 2) 把 public/ 推到 gh-pages 分支（用 git worktree，避免影响当前分支）
$tmp = ".gh-pages-deploy"
if (Test-Path $tmp) { git worktree remove $tmp --force 2>$null }
git worktree add -f $tmp gh-pages
try {
    Get-ChildItem $tmp -Force | Where-Object { $_.Name -ne ".git" } | Remove-Item -Recurse -Force
    robocopy "public" $tmp /E /NFL /NDL /NJH /NJS | Out-Null
    New-Item -ItemType File -Path (Join-Path $tmp ".nojekyll") -Force | Out-Null

    git -C $tmp add -A
    git -C $tmp -c user.name="sshuo" -c user.email="sshuo@users.noreply.github.com" `
        commit -m ("deploy: " + (Get-Date -Format "yyyy-MM-dd HH:mm"))
    Write-Host "==> 推送到 gh-pages" -ForegroundColor Cyan
    git -C $tmp push origin gh-pages
    if ($LASTEXITCODE -ne 0) { throw "推送失败（可能需要配置代理，见 README）" }
} finally {
    Set-Location $PSScriptRoot
    git worktree remove $tmp --force 2>$null
}

Write-Host "==> 完成。约 1~2 分钟后访问 https://www.sshuo.cc 查看（Pages 构建需几十秒）" -ForegroundColor Green
