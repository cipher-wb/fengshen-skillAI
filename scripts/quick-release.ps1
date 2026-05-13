# scripts/quick-release.ps1
# 一键发版脚本 (Windows PowerShell)
# 用途：mental_model 学完一批后快速发 patch 版本
#
# 用法：
#   pwsh scripts/quick-release.ps1                 # patch bump (默认)
#   pwsh scripts/quick-release.ps1 -BumpType minor # minor bump
#   pwsh scripts/quick-release.ps1 -DryRun         # 只 show 不真发

param(
    [string]$BumpType = "patch",
    [switch]$DryRun = $false,
    [string]$CommitMessage = ""
)

$ErrorActionPreference = "Stop"

function Step($n, $msg) {
    Write-Host "`n[$n] $msg" -ForegroundColor Cyan
}

function Run($cmd) {
    Write-Host "  $cmd" -ForegroundColor Gray
    if (-not $DryRun) {
        Invoke-Expression $cmd
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Command failed" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }
}

Write-Host "═════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  fengshen-skillai quick-release" -ForegroundColor Cyan
Write-Host "  Bump type: $BumpType / Dry run: $DryRun" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════" -ForegroundColor Cyan

Step 1 "抽源 (extract templates from F:/DreamRivakes2/...)"
Run "node scripts/extract-from-source.js"

Step 2 "跑 e2e 测试"
Run "node scripts/test-init.js"

Step 3 "跑 unit 测试"
Run "npm test"

Step 4 "$BumpType bump version"
if (-not $DryRun) {
    npm version $BumpType --no-git-tag-version
    $newVersion = (Get-Content package.json | ConvertFrom-Json).version
    Write-Host "  新版本: $newVersion" -ForegroundColor Green
} else {
    $newVersion = "X.Y.Z (dry-run)"
}

Step 5 "Git commit + tag + push"
if ($CommitMessage -eq "") {
    $CommitMessage = "v$newVersion`: mental_model 学习更新"
}
Run "git add ."
Run "git commit -m `"$CommitMessage`""
Run "git tag v$newVersion"
Run "git push origin main --tags"

Step 6 "GitHub Release"
Run "gh release create v$newVersion --title `"v$newVersion`" --notes-file CHANGELOG.md"

Step 7 "npm publish"
Run "npm publish"

Step 8 "验证"
Run "npx fengshen-skillai@latest version"

Write-Host "`n═════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  发版完成 ✓  v$newVersion" -ForegroundColor Green
Write-Host "═════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "用户安装：" -ForegroundColor Gray
Write-Host "  npx fengshen-skillai@latest init <path>" -ForegroundColor White
