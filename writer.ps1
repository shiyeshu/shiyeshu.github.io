# 松鼠A的博客 · 文章编写器 启动脚本
# 用法：右键「使用 PowerShell 运行」，或双击同目录的 writer.cmd
# 可选参数：-Port 7312（默认 7311）
param(
    [int]$Port = 7311
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Server = Join-Path $Root 'tools\writer\server.py'

if (-not (Test-Path $Server)) {
    throw "找不到 server.py：$Server"
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    throw '找不到 python，请先安装 Python 3 并加入 PATH'
}

Write-Host ''
Write-Host '  ✍️  松鼠A的博客 · 文章编写器' -ForegroundColor Cyan
Write-Host "  站点：$Root"
Write-Host "  端口：$Port"
Write-Host '  浏览器会自动打开；关闭本窗口或 Ctrl+C 即可停止。' -ForegroundColor DarkGray
Write-Host ''

& $Python.Source $Server --port $Port --open
