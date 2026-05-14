# scripts/quick-release.ps1
# 一键发版脚本 (Windows PowerShell / v2 / 含自动 batch_buffer tarball 上传)
# 用途：mental_model 学完一批后快速发 patch 版本
#
# 用法：
#   pwsh scripts/quick-release.ps1                 # patch bump (默认)
#   pwsh scripts/quick-release.ps1 -BumpType minor # minor bump
#   pwsh scripts/quick-release.ps1 -DryRun         # 只 show 不真发
#   pwsh scripts/quick-release.ps1 -ForceTarball   # 强制重新生成 + 上传完整学习痕迹 tarball
#                                                  # (默认仅当 mental_model 版本变化时自动触发)
#   pwsh scripts/quick-release.ps1 -SkipTarball    # 跳过 tarball 步骤 (即使 mental_model 变了)

param(
    [string]$BumpType = "patch",
    [switch]$DryRun = $false,
    [string]$CommitMessage = "",
    [switch]$ForceTarball = $false,
    [switch]$SkipTarball = $false
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
Write-Host "  fengshen-skillai quick-release v2 (含自动 tarball)" -ForegroundColor Cyan
Write-Host "  Bump: $BumpType / Dry-run: $DryRun" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════" -ForegroundColor Cyan

# ────────────────────────────────────────────
# 检测 mental_model 版本（决定是否需要重新打 tarball）
# ────────────────────────────────────────────
$pkgBefore = Get-Content package.json | ConvertFrom-Json
$oldMentalModelVersion = $pkgBefore.fengshenMentalModelVersion
Write-Host "`n[检测] 当前 mental_model_version = $oldMentalModelVersion" -ForegroundColor Yellow

Step 1 "抽源 (extract templates from F:/DreamRivakes2/...)"
Run "node scripts/extract-from-source.js"

# 抽源后读源工程的 mental_model 真实版本号
$newMentalModelVersion = $oldMentalModelVersion  # default
$mmReadmePath = "templates/_doc/SkillAI/mental_model/README.md"
if (Test-Path $mmReadmePath) {
    $mmContent = Get-Content $mmReadmePath -Raw
    if ($mmContent -match "mental_model_version[:：]\s*(v[\d.]+)") {
        $newMentalModelVersion = $matches[1]
    }
}
Write-Host "[检测] 源工程 mental_model_version = $newMentalModelVersion" -ForegroundColor Yellow

# 判定是否要打 tarball
$mentalModelChanged = ($oldMentalModelVersion -ne $newMentalModelVersion)
$needTarball = $false
if ($SkipTarball) {
    Write-Host "[判定] -SkipTarball / 跳过 tarball 步骤" -ForegroundColor Yellow
} elseif ($ForceTarball) {
    Write-Host "[判定] -ForceTarball / 强制重生成 tarball" -ForegroundColor Yellow
    $needTarball = $true
} elseif ($mentalModelChanged) {
    Write-Host "[判定] mental_model 版本变化 $oldMentalModelVersion → $newMentalModelVersion / 自动重生成 tarball" -ForegroundColor Yellow
    $needTarball = $true
} else {
    Write-Host "[判定] mental_model 未变 / 跳过 tarball (用 -ForceTarball 强制)" -ForegroundColor Yellow
}

# 如果 mental_model 版本变了 / 同步 package.json
if ($mentalModelChanged -and -not $DryRun) {
    Step "1.5" "同步 package.json#fengshenMentalModelVersion → $newMentalModelVersion"
    $pkg = Get-Content package.json -Raw | ConvertFrom-Json
    $pkg.fengshenMentalModelVersion = $newMentalModelVersion
    $pkg | ConvertTo-Json -Depth 10 | Set-Content package.json -NoNewline
    "`n" | Out-File -Append -NoNewline package.json   # 文件末尾加个换行
}

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

# ────────────────────────────────────────────
# Step 5 - 准备完整学习痕迹 tarball (仅 mental_model 变化时)
# ────────────────────────────────────────────
$tarballPath = ""
$tarballShaPath = ""
if ($needTarball) {
    Step "5a" "生成完整学习痕迹 tarball (~3-44 MB / mental_model $newMentalModelVersion)"
    Run "node scripts/prepare-release-tarball.js"
    $tarballPath = "fengshen-learning-history-$newMentalModelVersion.tar.gz"
    $tarballShaPath = "$tarballPath.sha256"

    Step "5b" "同步 sha256 到 package.json"
    if (-not $DryRun -and (Test-Path $tarballPath)) {
        $sha = (Get-FileHash $tarballPath -Algorithm SHA256).Hash.ToLower()
        $pkg = Get-Content package.json -Raw | ConvertFrom-Json
        $pkg.fengshenLearningHistorySha256 = $sha
        $pkg | ConvertTo-Json -Depth 10 | Set-Content package.json -NoNewline
        "`n" | Out-File -Append -NoNewline package.json
        Write-Host "  sha256 = $sha" -ForegroundColor Green
    }
}

Step 6 "Git commit + tag + push"
if ($CommitMessage -eq "") {
    if ($needTarball) {
        $CommitMessage = "v$newVersion`: mental_model $newMentalModelVersion + tarball 更新"
    } else {
        $CommitMessage = "v$newVersion`: 文档/CLI 优化 (mental_model 未变 / 维持 $newMentalModelVersion)"
    }
}
Run "git add ."
Run "git commit -m `"$CommitMessage`""
Run "git tag v$newVersion"
# Windows 用 git 代理时 push 需绕开
Run "git -c http.proxy= -c https.proxy= push origin main --tags"

Step 7 "GitHub Release (含 tarball 如有)"
if ($needTarball -and (Test-Path $tarballPath)) {
    Write-Host "  挂 tarball: $tarballPath" -ForegroundColor Green
    Run "gh release create v$newVersion --title `"v$newVersion`" --notes-file CHANGELOG.md $tarballPath $tarballShaPath"
} else {
    Run "gh release create v$newVersion --title `"v$newVersion`" --notes-file CHANGELOG.md"
}

Step 8 "npm publish (含 retry)"
if (-not $DryRun) {
    $maxRetry = 3
    for ($i = 1; $i -le $maxRetry; $i++) {
        Write-Host "  publish 尝试 $i/$maxRetry..." -ForegroundColor Gray
        $output = npm publish --access public 2>&1
        $output | Out-Host
        if ($output -match "\+ fengshen-skillai@$newVersion") {
            Write-Host "  ✓ npm publish 成功" -ForegroundColor Green
            break
        }
        if ($i -lt $maxRetry) {
            Write-Host "  ⚠ 失败 / 3 秒后重试..." -ForegroundColor Yellow
            Start-Sleep -Seconds 3
        }
    }
}

Step 9 "验证"
Run "npx fengshen-skillai@latest version"

Write-Host "`n═════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  发版完成 ✓  v$newVersion" -ForegroundColor Green
if ($needTarball) {
    Write-Host "  含 tarball: $tarballPath" -ForegroundColor Green
}
Write-Host "═════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "用户安装：" -ForegroundColor Gray
Write-Host "  npx fengshen-skillai@latest init <path>" -ForegroundColor White
if ($needTarball) {
    Write-Host "用户拉完整学习痕迹：" -ForegroundColor Gray
    Write-Host "  npx fengshen-skillai download-history" -ForegroundColor White
}
