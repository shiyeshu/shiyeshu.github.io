# =============================================================================
# 一键发布：构建 Hugo 站点 → 推送到 gh-pages 分支 → 触发并等待 GitHub Pages 构建
#
# 当前部署方式：GitHub Pages 从 gh-pages 分支发布（Actions 故障期间的应急方案，
# 详见 README 第四节）。日常写文章后，在仓库根目录运行：
#
#     .\deploy.ps1
#
# 脚本会自动：
#   1. 用 Hugo 0.167 构建 public/
#   2. 把产物提交到 gh-pages 分支并推送
#   3. 触发 Pages 构建并等待完成，最后打印线上地址
#
# 如果本机访问 GitHub 需要代理（默认检测 127.0.0.1:7890），脚本会自动给 git push
# 加上代理参数，不需要改全局 git 配置。
# =============================================================================
param(
    # 跳过构建，仅推送现有 public/
    [switch]$SkipBuild,
    # 只构建和检查差异，不推送、不触发 Pages
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# ---------------------------------------------------------------- 1. 找 Hugo
$hugoExe = $null
if (Get-Command hugo -ErrorAction SilentlyContinue) {
    $hugoExe = "hugo"
} elseif (Test-Path "..\tools\hugo167\hugo.exe") {
    $hugoExe = "..\tools\hugo167\hugo.exe"
} elseif (Test-Path "..\tools\hugo\hugo.exe") {
    $hugoExe = "..\tools\hugo\hugo.exe"
} else {
    throw "找不到 hugo.exe：请安装 Hugo extended 0.167.0，或确认 ..\tools\hugo167\hugo.exe 存在"
}

if (-not $SkipBuild) {
    Write-Host "==> 构建站点" -ForegroundColor Cyan
    & $hugoExe --gc --minify
    if ($LASTEXITCODE -ne 0) { throw "Hugo 构建失败" }
}

# ---------------------------------------------------------------- 2. 代理检测
$proxy = $null
$configuredProxy = (git config --get http.proxy) 2>$null
if (-not $configuredProxy -and (Test-NetConnection 127.0.0.1 -Port 7890 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    $proxy = "http://127.0.0.1:7890"
    Write-Host "==> 检测到本地代理，git 推送将使用 $proxy" -ForegroundColor DarkGray
}
$gitNet = @()
if ($proxy) { $gitNet = @("-c", "http.proxy=$proxy") }

# ---------------------------------------------------------------- 3. 更新 gh-pages
$tmp = ".gh-pages-deploy"
if (Test-Path $tmp) { git worktree remove $tmp --force 2>$null }
git worktree add --detach $tmp origin/gh-pages | Out-Null
if ($LASTEXITCODE -ne 0) { throw "无法创建 gh-pages worktree（请检查 origin/gh-pages 是否存在）" }

$pushed = $false
try {
    Get-ChildItem $tmp -Force | Where-Object { $_.Name -ne ".git" } | Remove-Item -Recurse -Force
    robocopy "public" $tmp /E /NFL /NDL /NJH /NJS | Out-Null
    New-Item -ItemType File -Path (Join-Path $tmp ".nojekyll") -Force | Out-Null

    git -C $tmp add -A
    $changes = git -C $tmp status --porcelain
    if (-not $changes) {
        Write-Host "==> 站点内容没有变化，跳过推送" -ForegroundColor Yellow
    } elseif ($DryRun) {
        Write-Host "==> DryRun：检测到以下变化，未推送" -ForegroundColor Yellow
        $changes | Select-Object -First 20
    } else {
        git -C $tmp -c user.name="sshuo" -c user.email="sshuo@users.noreply.github.com" `
            commit -m ("deploy: " + (Get-Date -Format "yyyy-MM-dd HH:mm")) | Out-Null
        Write-Host "==> 推送到 gh-pages" -ForegroundColor Cyan
        git -C $tmp @gitNet push origin "HEAD:gh-pages"
        if ($LASTEXITCODE -ne 0) { throw "推送失败：请检查网络/代理（当前代理：$proxy）" }
        $pushed = $true
    }
} finally {
    Set-Location $PSScriptRoot
    git worktree remove $tmp --force 2>$null
}

if (-not $pushed) {
    Write-Host "==> 没有推送，发布结束（线上内容未变）" -ForegroundColor Green
    exit 0
}

# ---------------------------------------------------------------- 4. 触发 Pages 构建
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py -and (Test-Path "tools\pages_build.py")) {
    Write-Host "==> 触发 GitHub Pages 构建" -ForegroundColor Cyan
    $env:PYTHONIOENCODING = "utf-8"
    & python "tools\pages_build.py"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "提示：脚本未能确认构建，请稍后手动查看 https://github.com/shiyeshu/shiyeshu.github.io/deployments" -ForegroundColor Yellow
    }
} else {
    Write-Host "==> 已推送。Pages 通常会在 1~2 分钟内自动构建，稍后访问 https://www.sshuo.cc" -ForegroundColor Green
}

Write-Host "==> 完成：https://www.sshuo.cc" -ForegroundColor Green
